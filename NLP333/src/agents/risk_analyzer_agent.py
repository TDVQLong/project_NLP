import os
import json
import re
from typing import Optional, List, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .schemas import RiskItem, RiskAnalysisResult, ReviewPerspective, ContractType
from ..retrieval.legal_kb import LegalKnowledgeBase

class RiskAnalyzerAgent:
    """
    Tầng 4: Agent 2 - Suy luận Legal NLI & Phân tích rủi ro.
    Áp dụng kiến trúc Dual-Track:
    - Luồng 1: So khớp quy tắc chuyên ngành đóng kín (42+ quy tắc).
    - Luồng 2: Vận dụng tri thức Pre-trained nền tảng (Foundation Legal NLI)
      để bắt trọn các điều khoản trái đạo đức xã hội (Điều 123 BLDS), lạm quyền hoặc phi lý cực đoan.
    """

    def __init__(
        self,
        contract_type: str = "rental",
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
        self.contract_type = contract_type
        self.kb = LegalKnowledgeBase(contract_type=contract_type)

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

    def _build_system_prompt(self, contract_type: str, perspective: str = "party_b") -> str:
        rules_text = []
        for r in self.kb.get_all_rules():
            rules_text.append(
                f"- [{r.rule_id}] {r.rule_name} (Mức độ: {r.risk_level})\n"
                f"  Điều kiện kích hoạt: {r.trigger_condition}\n"
                f"  Căn cứ luật: {r.legal_basis}\n"
                f"  Giải thích: {r.explanation}"
            )
        rules_block = "\n".join(rules_text)

        doc_name = "lao động" if contract_type == "employment" else "thuê nhà"
        return f"""Bạn là Cố vấn Pháp lý chuyên sâu (Legal Advisor) hỗ trợ rà soát và tham vấn hợp đồng {doc_name} tại Việt Nam.
Góc nhìn rà soát: {perspective} (Ưu tiên tham vấn bảo vệ quyền và lợi ích hợp pháp, phòng ngừa rủi ro tranh chấp và cân bằng nghĩa vụ).

PHONG THÁI TƯ VẤN:
- Cẩn trọng, khiêm nhường, khách quan và mang tính xây dựng.
- Sử dụng ngôn ngữ tham vấn nhã nhặn: "Theo quy định pháp luật hiện hành và chuẩn mực thực tiễn...", "Theo tôi được biết, điều khoản này có thể tiềm ẩn rủi ro hoặc gây bất lợi...", "Khuyến nghị hai bên cân nhắc điều chỉnh để hài hòa quyền lợi...".

DANH MỤC CÁC QUY TẮC PHÁP LÝ THAM KHẢO (KB):
{rules_block}

NGUYÊN TẮC THẨM ĐỊNH MỞ (FOUNDATION LEGAL REASONING & GENERAL PRINCIPLES):
1. Bên cạnh các quy tắc chuyên ngành cụ thể, bạn hãy tự nhiên vận dụng tri thức pháp lý và đạo đức nền tảng:
   - Nguyên tắc bình đẳng, thiện chí, trung thực và tôn trọng quyền lợi hợp pháp của nhau (Điều 3 Bộ luật Dân sự 2015).
   - Quyền nhân thân, bảo vệ danh dự, nhân phẩm, uy tín và sự toàn vẹn thân thể của con người (Điều 33, Điều 34 BLDS 2015).
   - Chuẩn mực đạo đức xã hội, trật tự công cộng và thuần phong mỹ tục (Điều 123 BLDS 2015).
2. Nếu phát hiện bất kỳ điều khoản nào có dấu hiệu bất thường, lạm quyền, áp đặt nghĩa vụ khẩn cấp phi lý, xâm phạm quyền nhân thân hoặc đi ngược lại chuẩn mực đạo đức xã hội:
   -> Hãy linh hoạt nhận diện và gắn cờ cảnh báo (sử dụng mã phù hợp như RULE_CIVIL_MORALITY_VIOLATION, RULE_ARBITRARY_UNILATERAL_DEMAND hoặc nhóm quy tắc liên quan) kèm theo lời giải thích thấu đáo, chừng mực và có căn cứ luật định.
3. TRÍCH DẪN NGUYÊN VĂN (VERBATIM CITATION):
   - Trường 'original_clause' BẮT BUỘC phải là câu văn trích dẫn CHÍNH XÁC NGUYÊN VĂN từ trong hợp đồng để làm bằng chứng tham vấn khách quan. Tuyệt đối không tự suy diễn hoặc bịa đặt câu chữ.
4. PHÂN LOẠI MỨC ĐỘ RỦI RO:
   - RED (Rủi ro cao): Trái điều cấm của luật, trái đạo đức xã hội (Điều 123 BLDS 2015, Luật Nhà ở 2023, BLLĐ 2019), điều khoản có nguy cơ vô hiệu tuyệt đối.
   - YELLOW (Cần lưu ý): Bất bình đẳng thương mại, thiếu rõ ràng, đẩy rủi ro bất hợp lý cho một bên.
5. Nếu hợp đồng sạch và tuân thủ chuẩn mực, trả về: is_safe=true, risks=[].
6. Trả về DUY NHẤT một chuỗi JSON hợp lệ khớp với JSON Schema.
"""

    def analyze(
        self,
        contract_text: str,
        contract_type: Optional[str] = None,
        perspective: str = "party_b"
    ) -> RiskAnalysisResult:
        if not contract_text or not contract_text.strip():
            raise ValueError("Văn bản hợp đồng rỗng.")

        # Xử lý an toàn nếu đầu vào là thông báo từ tầng Ingestion/OCR
        if contract_text.strip().startswith("[CẢNH BÁO"):
            return RiskAnalysisResult(
                is_safe=False,
                total_risks=1,
                red_risks_count=0,
                yellow_risks_count=1,
                risks=[RiskItem(
                    rule_id="RULE_INPUT_INGESTION_NOTICE",
                    rule_name="Thông báo từ tầng nạp tài liệu (Ingestion/OCR)",
                    category="Đầu vào tài liệu",
                    risk_level="YELLOW",
                    original_clause=contract_text[:200],
                    legal_basis="Kiểm tra cấu hình API Key hoặc định dạng tệp",
                    explanation=contract_text,
                    suggested_action="Vui lòng kiểm tra lại cấu hình OPENROUTER_API_KEY trong .env hoặc nạp tệp hợp đồng (.docx, .pdf, .txt)."
                )],
                overall_assessment="Chưa thể phân tích nội dung do tệp đầu vào gặp thông báo cảnh báo từ tầng bóc tách."
            )

        # Giới hạn an toàn độ dài văn bản để tránh tràn context token (> 100.000 ký tự)
        if len(contract_text) > 100000:
            contract_text = contract_text[:100000]

        active_type = contract_type or self.contract_type
        if active_type != self.kb.contract_type:
            self.kb.switch_domain(active_type)

        if not self.client:
            return self._rule_based_fallback_analyze(contract_text)

        system_prompt = self._build_system_prompt(active_type, perspective)
        schema_json = json.dumps(RiskAnalysisResult.model_json_schema(), ensure_ascii=False)

        user_prompt = (
            f"Văn bản hợp đồng cần rà soát:\n---\n{contract_text}\n---\n\n"
            f"Đối chiếu từng điều khoản với bộ quy tắc luật và tri thức pháp lý nền tảng để trả về JSON theo schema:\n{schema_json}"
        )

        try:
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
            if raw_json_str.startswith("```"):
                raw_json_str = re.sub(r"^```(?:json)?\n?", "", raw_json_str)
                raw_json_str = re.sub(r"\n?```$", "", raw_json_str)

            result = RiskAnalysisResult.model_validate_json(raw_json_str)

            for risk in result.risks:
                rule_obj = self.kb.get_rule(risk.rule_id)
                if rule_obj:
                    if not risk.statutory_citation and rule_obj.statutory_citation:
                        risk.statutory_citation = rule_obj.statutory_citation
                    if not risk.reference_url and rule_obj.reference_url:
                        risk.reference_url = rule_obj.reference_url

            result.total_risks = len(result.risks)
            result.red_risks_count = sum(1 for r in result.risks if r.risk_level.upper() == "RED")
            result.yellow_risks_count = sum(1 for r in result.risks if r.risk_level.upper() == "YELLOW")
            result.is_safe = (result.total_risks == 0)

            return result

        except Exception as e:
            print(f"⚠️ [API Notice - RiskAnalyzer]: Gọi mô hình '{self.model_name}' gặp vấn đề ({e}). Tự động kích hoạt cơ chế Fallback Rule-based & Legal KB...")
            return self._rule_based_fallback_analyze(contract_text)

    def _rule_based_fallback_analyze(self, contract_text: str) -> RiskAnalysisResult:
        risks = []
        text_lower = contract_text.lower()

        for rule in self.kb.get_all_rules():
            for kw in rule.keywords:
                if kw.lower() in text_lower:
                    match = re.search(r"([^;\n\r]*?" + re.escape(kw) + r"[^;\n\r]*)", contract_text, re.IGNORECASE)
                    snippet = match.group(1).strip() if match else f"Điều khoản liên quan đến '{kw}'"
                    risks.append(RiskItem(
                        rule_id=rule.rule_id,
                        rule_name=rule.rule_name,
                        category=rule.category,
                        risk_level=rule.risk_level,
                        original_clause=snippet,
                        legal_basis=rule.legal_basis,
                        explanation=rule.explanation,
                        suggested_action=rule.suggested_clause,
                        statutory_citation=rule.statutory_citation,
                        reference_url=rule.reference_url,
                        nli_relation="CONTRADICTION" if rule.risk_level == "RED" else "UNFAIR"
                    ))
                    break

        return RiskAnalysisResult(
            is_safe=(len(risks) == 0),
            total_risks=len(risks),
            red_risks_count=sum(1 for r in risks if r.risk_level == "RED"),
            yellow_risks_count=sum(1 for r in risks if r.risk_level == "YELLOW"),
            risks=risks,
            overall_assessment=f"Phát hiện {len(risks)} điều khoản rủi ro qua cơ sở tri thức pháp luật chuẩn."
        )
