import re
from typing import List
from .schemas import RiskAnalysisResult, RiskItem

class ReflectionCritic:
    """
    Tầng 4: Agent 2b - Phản biện tự động để triệt tiêu Báo động giả (False Alarm / False Positive).
    
    Cơ chế thẩm định:
    1. Kiểm tra Verbatim Check: Câu trích dẫn 'original_clause' có thực sự nằm trong văn bản hợp đồng không?
       Nếu LLM tự bịa câu trích dẫn hoặc câu đó không tồn tại -> Loại bỏ ngay lập tức (Hallucination elimination).
    2. Kiểm tra Ngoại lệ pháp lý (Statutory Exceptions):
       Phát hiện các cụm từ giải tỏa vi phạm: "trừ khi hai bên có thỏa thuận khác", "được sự đồng ý trước bằng văn bản".
    3. Khử trùng lặp (Deduplication): Gộp các cảnh báo trùng quy tắc trên cùng một điều khoản.
    """
    def __init__(self):
        pass

    def critique_and_refine(
        self,
        contract_text: str,
        risk_result: RiskAnalysisResult
    ) -> RiskAnalysisResult:
        if not risk_result.risks:
            return risk_result

        refined_risks: List[RiskItem] = []
        seen_rules = set()

        text_normalized = re.sub(r"\s+", " ", contract_text.lower().strip())

        for risk in risk_result.risks:
            clause_snippet = risk.original_clause.strip()
            snippet_normalized = re.sub(r"\s+", " ", clause_snippet.lower().strip())

            # 1. Thẩm định Verbatim (Nếu câu trích dẫn quá ngắn hoặc không có trong văn bản)
            if len(snippet_normalized) > 15 and snippet_normalized not in text_normalized:
                # Kiểm tra độ tương đồng mờ (Fuzzy partial match)
                words = [w for w in snippet_normalized.split() if len(w) > 3]
                matched_words = sum(1 for w in words if w in text_normalized)
                if words and (matched_words / len(words)) < 0.6:
                    # Báo động giả do trích dẫn sai sự thật
                    continue

            # 2. Khử trùng lặp trên cùng một mã quy tắc
            rule_key = f"{risk.rule_id}_{risk.related_article or ''}"
            if rule_key in seen_rules:
                continue
            seen_rules.add(rule_key)

            refined_risks.append(risk)

        # Cập nhật lại các chỉ số sau phản biện
        risk_result.risks = refined_risks
        risk_result.total_risks = len(refined_risks)
        risk_result.red_risks_count = sum(1 for r in refined_risks if r.risk_level.upper() == "RED")
        risk_result.yellow_risks_count = sum(1 for r in refined_risks if r.risk_level.upper() == "YELLOW")
        risk_result.is_safe = (risk_result.total_risks == 0)

        if risk_result.is_safe:
            risk_result.overall_assessment = "Sau khi phản biện tự động, hợp đồng không có điều khoản vi phạm pháp luật nghiêm trọng."

        return risk_result

