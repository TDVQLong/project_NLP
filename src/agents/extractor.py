import os
import json
import re
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

from src.agents.schemas import ContractMetadata

# Load biến môi trường từ .env
load_dotenv()

EXTRACTION_SYSTEM_PROMPT = """Bạn là Chuyên gia Trích xuất Dữ liệu Pháp lý (Legal Extractor Agent) chuyên về Hợp đồng thuê nhà và phòng trọ tại Việt Nam.

Nhiệm vụ của bạn là đọc kỹ toàn bộ nội dung hợp đồng và trích xuất chính xác các thông tin có cấu trúc sau:
1. lessor_name: Họ tên đầy đủ của Bên cho thuê (Bên A / Chủ nhà / Bên đại diện).
2. lessee_name: Họ tên đầy đủ của Bên thuê (Bên B / Khách thuê).
3. property_address: Địa chỉ cụ thể của phòng trọ, căn hộ hoặc nhà cho thuê.
4. rent_price: Giá thuê hàng tháng tính bằng số thực VNĐ (Ví dụ: "4.500.000 đ", "4,5 triệu", "Bốn triệu năm trăm nghìn đồng" -> 4500000.0).
5. deposit_amount: Số tiền đặt cọc (hoặc tiền thế chân) tính bằng số thực VNĐ. Nếu hợp đồng ghi "cọc 01 tháng" thì lấy bằng giá thuê 1 tháng.
6. lease_term_months: Thời hạn hợp đồng tính theo số tháng (Ví dụ: "01 năm" -> 12, "06 tháng" -> 6).
7. start_date: Ngày bắt đầu có hiệu lực (định dạng DD/MM/YYYY).
8. end_date: Ngày kết thúc hợp đồng (định dạng DD/MM/YYYY).
9. payment_cycle: Chu kỳ thanh toán (Ví dụ: "Hàng tháng", "3 tháng/lần", "Vào ngày 05 hàng tháng").
10. payment_deadline_day: Ngày đến hạn thanh toán trong tháng nếu có (Ví dụ: "ngày 5 hàng tháng" -> 5).
11. notice_period_days: Số ngày phải thông báo trước khi muốn đơn phương chấm dứt hợp đồng (Ví dụ: "báo trước 30 ngày" -> 30, "báo trước 15 ngày" -> 15). Mặc định là 30 nếu không ghi rõ.
12. electricity_price: Đơn giá điện (Ví dụ: "3.800 đ/kWh", "4.000 đ/số").
13. water_price: Đơn giá nước (Ví dụ: "100.000 đ/người/tháng", "30.000 đ/khối").
14. termination_clause_summary: Tóm tắt 1-2 câu về điều kiện chấm dứt hợp đồng và hoàn cọc theo hợp đồng.

QUY TẮC BẮT BUỘC:
- Trả về DUY NHẤT một chuỗi JSON hợp lệ khớp với JSON Schema được yêu cầu. Không thêm văn bản giải thích ngoài JSON.
- Không bịa đặt thông tin. Nếu hợp đồng không đề cập trường nào, hãy để giá trị null.
- Với các trường số tiền (rent_price, deposit_amount), luôn chuyển về số nguyên/thực VNĐ, không để chữ kèm theo.
"""

class ExtractorAgent:
    """Agent 1: Chuyên trách đọc văn bản hợp đồng và trích xuất Metadata có cấu trúc."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        # Ưu tiên lấy từ OpenRouter trước nếu có
        self.api_key = (
            api_key 
            or os.getenv("OPENROUTER_API_KEY") 
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )
        self.base_url = (
            base_url 
            or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        )
        self.model_name = (
            model_name 
            or os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        )

        if self.api_key:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        else:
            self.client = None

    def extract(self, contract_text: str) -> ContractMetadata:
        """
        Trích xuất thông tin có cấu trúc từ văn bản hợp đồng thô.
        """
        if not contract_text or not contract_text.strip():
            raise ValueError("Nội dung hợp đồng rỗng, không thể trích xuất.")

        if not self.client:
            raise ValueError(
                "Chưa tìm thấy OPENROUTER_API_KEY trong file .env. "
                "Vui lòng kiểm tra lại cấu hình."
            )

        schema_json = json.dumps(ContractMetadata.model_json_schema(), ensure_ascii=False)
        user_prompt = (
            f"Dưới đây là toàn bộ nội dung văn bản hợp đồng thuê nhà:\n\n"
            f"---\n{contract_text}\n---\n\n"
            f"Hãy trích xuất thông tin và trả về đúng JSON Schema sau:\n{schema_json}"
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        raw_json_str = response.choices[0].message.content.strip()
        
        # Làm sạch nếu model bọc trong ```json ... ```
        if raw_json_str.startswith("```"):
            raw_json_str = re.sub(r"^```(?:json)?\n?", "", raw_json_str)
            raw_json_str = re.sub(r"\n?```$", "", raw_json_str)

        # Parse kết quả thành Pydantic object
        return ContractMetadata.model_validate_json(raw_json_str)
