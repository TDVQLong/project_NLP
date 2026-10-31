import os
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from src.agents.schemas import RiskItem, RiskAnalysisResult

load_dotenv()

class RiskAnalyzerAgent:
    """Agent 2: Chuyên gia rà soát rủi ro pháp lý & thương mại, đối chiếu với Bộ quy tắc luật đóng kín."""

    def __init__(
        self,
        rules_path: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
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

        # Nạp bộ quy tắc luật đóng kín (Closed Knowledge Base)
        self.rules_path = rules_path or os.path.join("data", "legal_rules.json")
        self.legal_rules = self._load_legal_rules()

    def _load_legal_rules(self) -> List[Dict[str, Any]]:
        """Nạp danh sách các quy tắc luật từ file JSON."""
        if not os.path.exists(self.rules_path):
            raise FileNotFoundError(f"Không tìm thấy file quy tắc luật tại: {self.rules_path}")

        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("rules", [])

    def _build_system_prompt(self) -> str:
        """Xây dựng System Prompt chứa trọn vẹn Bộ quy tắc luật đóng kín."""
        rules_summary = []
        for r in self.legal_rules:
            item_text = (
                f"- [MÃ: {r['rule_id']}] ({r['risk_level']}) {r['rule_name']}\n"
                f"  + Căn cứ: {r['legal_basis']}\n"
                f"  + Dấu hiệu vi phạm: {r['trigger_condition']}\n"
                f"  + Giải thích: {r['explanation']}"
            )
            rules_summary.append(item_text)

        all_rules_str = "\n".join(rules_summary)

        prompt = f"""Bạn là Giám đốc Pháp chế và Luật sư chuyên gia cao cấp về Hợp đồng Bất động sản tại Việt Nam.

Nhiệm vụ của bạn là rà soát kỹ lưỡng toàn văn hợp đồng thuê nhà được cung cấp, đối chiếu từng điều khoản với BỘ QUY TẮC LUẬT ĐÓNG KÍN (Closed Legal Knowledge Base - {len(self.legal_rules)} Quy tắc) dưới đây:

--- BỘ QUY TẮC LUẬT ĐÓNG KÍN ({len(self.legal_rules)} RULES) ---
{all_rules_str}
---------------------------------------------

QUY TẮC BẮT BUỘC KHI RÀ SOÁT:
1. NGUYÊN TẮC TRÍCH DẪN NGUYÊN VĂN (VERBATIM CITATION):
   - Trường 'original_clause' BẮT BUỘC phải là câu văn hoặc đoạn văn trích dẫn CHÍNH XÁC NGUYÊN VĂN từ trong văn bản hợp đồng.
   - TUYỆT ĐỐI KHÔNG TỰ DIỄN GIẢI, không tóm tắt hay bịa đặt câu chữ không có trong văn bản hợp đồng.
2. NGUYÊN TẮC PHÂN LOẠI MỨC ĐỘ RỦI RO:
   - 'RED' (Rủi ro Cao): Vi phạm trực tiếp điều cấm của pháp luật (Hiến pháp, BLDS 2015, Luật Nhà ở 2023), điều khoản vô hiệu.
   - 'YELLOW' (Rủi ro Trung bình): Bất bình đẳng thương mại, đẩy rủi ro vô lý cho người thuê, câu chữ mập mờ có nguy cơ thiệt hại.
3. TRƯỜNG HỢP HỢP ĐỒNG SẠCH (NEGATIVE CASE):
   - Nếu toàn bộ các điều khoản trong hợp đồng đều tuân thủ đúng pháp luật và cân bằng quyền lợi (như mẫu chuẩn của Bộ Xây dựng), hãy trả về:
     is_safe = true, total_risks = 0, red_risks_count = 0, yellow_risks_count = 0, risks = []
     overall_assessment: "Hợp đồng tuân thủ đúng pháp luật, các điều khoản rõ ràng, bình đẳng, không phát hiện rủi ro pháp lý."
4. ĐỊNH DẠNG ĐẦU RA:
   - Trả về DUY NHẤT một chuỗi JSON hợp lệ khớp với JSON Schema được yêu cầu. Không thêm văn bản chào hỏi hay giải thích ngoài JSON.
"""
        return prompt

    def analyze(self, contract_text: str) -> RiskAnalysisResult:
        """
        Rà soát toàn văn hợp đồng và trả về danh sách rủi ro kèm giải thích pháp lý.
        """
        if not contract_text or not contract_text.strip():
            raise ValueError("Văn bản hợp đồng rỗng, không thể rà soát.")

        if not self.client:
            raise ValueError("Chưa cấu hình API Key trong file .env để chạy RiskAnalyzerAgent.")

        system_prompt = self._build_system_prompt()
        schema_json = json.dumps(RiskAnalysisResult.model_json_schema(), ensure_ascii=False)

        user_prompt = (
            f"Dưới đây là toàn văn hợp đồng thuê nhà cần rà soát:\n\n"
            f"```text\n{contract_text}\n```\n\n"
            f"Hãy đối chiếu với {len(self.legal_rules)} quy tắc luật và trả về kết quả rà soát đúng theo JSON Schema sau:\n{schema_json}"
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
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
        result = RiskAnalysisResult.model_validate_json(raw_json_str)

        # Tự động gán Citation và Reference URL chính thức từ Legal Knowledge Base
        rules_map = {r["rule_id"]: r for r in self.legal_rules}
        for risk in result.risks:
            if risk.rule_id in rules_map:
                ref_rule = rules_map[risk.rule_id]
                if not risk.reference_url:
                    risk.reference_url = ref_rule.get("reference_url")
                if not risk.statutory_citation:
                    risk.statutory_citation = ref_rule.get("statutory_citation")

        # Đảm bảo tính toán số lượng chính xác
        result.total_risks = len(result.risks)
        result.red_risks_count = sum(1 for r in result.risks if r.risk_level.upper() == "RED")
        result.yellow_risks_count = sum(1 for r in result.risks if r.risk_level.upper() == "YELLOW")
        result.is_safe = (result.total_risks == 0)

        return result
