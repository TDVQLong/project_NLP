import os
import json
import re
from typing import Optional, List, Dict, Any, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .schemas import (
    ContractMetadata,
    EmploymentMetadata,
    RiskItem,
    RiskAnalysisResult,
    RedlineProposal,
    ContractReviewPackage
)
from ..retrieval.legal_kb import LegalKnowledgeBase

class ProposalAgent:
    """
    Tầng 4: Agent 3 - Soạn thảo Redlining & Kịch bản đàm phán 3 bước.
    Tổng hợp báo cáo, tính điểm an toàn (Safety Score), tạo câu sửa đổi pháp lý và chuẩn bị gói hồ sơ duyệt HITL.
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

    def _calculate_safety_score(self, red_count: int, yellow_count: int) -> float:
        score = 10.0 - (red_count * 2.5) - (yellow_count * 1.0)
        return max(1.0, min(10.0, round(score, 1)))

    def _determine_verdict(self, red_count: int, yellow_count: int, score: float) -> str:
        if red_count == 0 and yellow_count == 0:
            return "AN TOÀN - ĐỦ ĐIỀU KIỆN KÝ KẾT"
        elif red_count > 0 or score < 5.0:
            return "RỦI RO CAO - CẦN ĐÀM PHÁN SỬA ĐỔI TRƯỚC KHI KÝ"
        else:
            return "CẦN ĐÀM PHÁN THỎA THUẬN LẠI MỘT SỐ ĐIỀU KHOẢN"

    def formulate_proposals(
        self,
        contract_text: str,
        risk_result: RiskAnalysisResult,
        metadata: Optional[Union[ContractMetadata, EmploymentMetadata]] = None,
        perspective: str = "party_b"
    ) -> ContractReviewPackage:
        red_count = risk_result.red_risks_count
        yellow_count = risk_result.yellow_risks_count
        score = self._calculate_safety_score(red_count, yellow_count)
        verdict = self._determine_verdict(red_count, yellow_count, score)

        if not risk_result.risks:
            return ContractReviewPackage(
                executive_summary="Hợp đồng tuân thủ tốt các quy định pháp luật. Không phát hiện điều khoản vi phạm điều cấm hoặc bất lợi nghiêm trọng.",
                verdict=verdict,
                safety_score=score,
                total_risks_found=0,
                proposals=[],
                is_hitl_completed=True,
                final_contract_text=contract_text
            )

        proposals: List[RedlineProposal] = []

        for idx, risk in enumerate(risk_result.risks, 1):
            rule_obj = self.kb.get_rule(risk.rule_id)
            suggested = rule_obj.suggested_clause if rule_obj else (risk.suggested_action or "Đề xuất sửa đổi điều khoản này theo quy định pháp luật hiện hành.")
            citation = risk.statutory_citation or (rule_obj.statutory_citation if rule_obj else risk.legal_basis)
            ref_url = risk.reference_url or (rule_obj.reference_url if rule_obj else None)

            if perspective == "party_b":
                script = f"Dạ em chào anh/chị, theo em được biết và tham khảo các quy định hiện hành tại {citation}, điều khoản này có thể phát sinh băn khoăn cho cả hai bên khi thực hiện. Em xin phép đề xuất mình điều chỉnh lại một chút thành: '{suggested}' để hợp đồng rõ ràng, đúng luật và an tâm cho đôi bên ạ."
                compromise = "Trường hợp cần thêm thời gian xem xét, hai bên có thể thỏa thuận lập Phụ lục làm rõ các điều kiện bảo đảm để cùng yên tâm hợp tác."
            else:
                script = f"Kính gửi đối tác, trên tinh thần thiện chí và theo các chuẩn mực pháp lý tại {citation}, chúng tôi khuyến nghị điều chỉnh câu chữ thành: '{suggested}' nhằm phòng ngừa rủi ro tranh chấp và đảm bảo tính minh bạch, hài hòa cho cả hai bên."
                compromise = "Thống nhất giữ nguyên mức bảo đảm cơ bản theo thông lệ thị trường."

            proposals.append(RedlineProposal(
                proposal_id=f"PROP_{idx:03d}",
                rule_id=risk.rule_id,
                rule_name=risk.rule_name,
                risk_level=risk.risk_level,
                related_article=risk.related_article,
                original_clause=risk.original_clause,
                proposed_clause=suggested,
                statutory_citation=citation,
                reference_url=ref_url,
                negotiation_script=script,
                compromise_option=compromise,
                hitl_status="PENDING"
            ))

        summary = f"Phát hiện tổng cộng {len(proposals)} điều khoản rủi ro ({red_count} điều khoản vi phạm luật cấm, {yellow_count} điều khoản bất lợi). Điểm an toàn: {score}/10."

        return ContractReviewPackage(
            executive_summary=summary,
            verdict=verdict,
            safety_score=score,
            total_risks_found=len(proposals),
            proposals=proposals,
            is_hitl_completed=False,
            final_contract_text=None
        )
