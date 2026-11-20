import os
import json
import re
from typing import Optional, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .schemas import ContractMetadata, EmploymentMetadata

EXTRACTION_SYSTEM_PROMPT = """Bạn là Chuyên gia Trích xuất Dữ liệu Pháp lý chuyên về Hợp đồng thuê nhà.
Trích xuất: lessor_name, lessee_name, property_address, rent_price, deposit_amount, lease_term_months, start_date, end_date, payment_cycle, notice_period_days.
Trả về duy nhất JSON hợp lệ theo schema.
"""

EMPLOYMENT_EXTRACTION_SYSTEM_PROMPT = """Bạn là Chuyên gia Trích xuất Dữ liệu Pháp lý chuyên về Hợp đồng Lao động.
Trích xuất: employer_name, employee_name, job_title, work_location, official_salary, probation_salary, probation_duration_days, working_hours, notice_period_days.
Trả về duy nhất JSON hợp lệ theo schema.
"""

class ExtractorAgent:
    """Tầng 4: Agent 1 - Bóc tách thông tin có cấu trúc từ văn bản hợp đồng."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = (
            api_key 
            or os.getenv("OPENROUTER_API_KEY")
            or os.getenv("GROQ_API_KEY") 
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )
        self.base_url = (
            base_url
            or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        )
        self.model_name = (
            model_name 
            or os.getenv("OPENROUTER_MODEL")
            or os.getenv("LLM_MODEL")
            or "google/gemini-2.5-flash"
        )
        self.client = None

        if self.api_key:
            if os.getenv("GROQ_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
                try:
                    from groq import Groq
                    self.client = Groq(api_key=self.api_key)
                except ImportError:
                    pass
            else:
                try:
                    from openai import OpenAI
                    self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
                except ImportError:
                    pass

    def extract(self, contract_text: str, contract_type: str = "rental") -> Union[ContractMetadata, EmploymentMetadata]:
        if not contract_text or not contract_text.strip():
            raise ValueError("Nội dung hợp đồng rỗng.")

        target_schema_cls = EmploymentMetadata if contract_type == "employment" else ContractMetadata
        sys_prompt = EMPLOYMENT_EXTRACTION_SYSTEM_PROMPT if contract_type == "employment" else EXTRACTION_SYSTEM_PROMPT

        if not self.client:
            return self._regex_fallback_extract(contract_text, contract_type)

        schema_json = json.dumps(target_schema_cls.model_json_schema(), ensure_ascii=False)
        user_prompt = (
            f"Văn bản hợp đồng:\n---\n{contract_text}\n---\n\n"
            f"Trích xuất thông tin theo đúng JSON Schema sau:\n{schema_json}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            raw_json_str = response.choices[0].message.content.strip()
            if raw_json_str.startswith("```"):
                raw_json_str = re.sub(r"^```(?:json)?\n?", "", raw_json_str)
                raw_json_str = re.sub(r"\n?```$", "", raw_json_str)

            return target_schema_cls.model_validate_json(raw_json_str)
        except Exception as e:
            print(f"⚠️ [API Notice - Extractor]: Gọi mô hình '{self.model_name}' gặp vấn đề ({e}). Tự động kích hoạt cơ chế Regex Fallback...")
            return self._regex_fallback_extract(contract_text, contract_type)

    def _regex_fallback_extract(self, text: str, contract_type: str):
        if contract_type == "employment":
            meta = EmploymentMetadata()
            emp_match = re.search(r"Bên A\s*[:\-\(]?\s*([^\n\.,]+)", text, re.IGNORECASE)
            if emp_match: meta.employer_name = emp_match.group(1).strip()
            sal_match = re.search(r"(?:mức lương|tiền lương)\s*[:\-\(]?\s*([\d\.\,]+)", text, re.IGNORECASE)
            if sal_match:
                try: meta.official_salary = float(sal_match.group(1).replace(".", "").replace(",", ""))
                except: pass
            return meta
        else:
            meta = ContractMetadata()
            lessor_match = re.search(r"Bên A\s*[:\-\(]?\s*([^\n\.,]+)", text, re.IGNORECASE)
            if lessor_match: meta.lessor_name = lessor_match.group(1).strip()
            price_match = re.search(r"(?:giá thuê|tiền thuê)\s*[:\-\(]?\s*([\d\.\,]+)", text, re.IGNORECASE)
            if price_match:
                try: meta.rent_price = float(price_match.group(1).replace(".", "").replace(",", ""))
                except: pass
            return meta
