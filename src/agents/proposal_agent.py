import os
import json
import re
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from src.agents.schemas import (
    ContractMetadata,
    RiskItem,
    RiskAnalysisResult,
    RedlineProposal,
    ContractReviewPackage
)

load_dotenv()

class ProposalAgent:
    """
    Agent 3: Chuyên gia Tổng hợp, Đánh giá Rủi ro, Đề xuất Sửa đổi (Redlining) 
    kèm Trích dẫn Pháp lý (Statutory Citation) và Hỗ trợ Cơ chế Duyệt Người-trong-vòng-lặp (HITL).
    """

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

        # Nạp cơ sở dữ liệu luật đóng kín để lấy mẫu chuẩn và link vbpl.vn
        self.rules_path = rules_path or os.path.join("data", "legal_rules.json")
        self.rules_map = self._load_rules_map()

    def _load_rules_map(self) -> Dict[str, Dict[str, Any]]:
        """Nạp dữ liệu quy tắc luật thành map theo rule_id."""
        if not os.path.exists(self.rules_path):
            return {}
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {r["rule_id"]: r for r in data.get("rules", [])}
        except Exception:
            return {}

    def _calculate_safety_score(self, red_count: int, yellow_count: int) -> float:
        """
        Tính thang điểm an toàn hợp đồng từ 1.0 đến 10.0:
        - Xuất phát điểm: 10.0 (Chuẩn mực)
        - Mỗi lỗi ĐỎ (vi phạm luật cấm): trừ 2.5 điểm
        - Mỗi lỗi VÀNG (bất lợi thương mại): trừ 1.0 điểm
        - Điểm sàn: tối thiểu 1.0 điểm.
        """
        score = 10.0 - (red_count * 2.5) - (yellow_count * 1.0)
        return max(1.0, min(10.0, round(score, 1)))

    def _determine_verdict(self, red_count: int, yellow_count: int, score: float) -> str:
        """Đưa ra phán quyết pháp lý tổng quan."""
        if red_count == 0 and yellow_count == 0:
            return "AN TOÀN - ĐỦ ĐIỀU KIỆN KÝ KẾT"
        elif red_count > 0 or score < 5.0:
            return "RỦI RO ĐẶC BIỆT CAO - CẦN ĐÀM PHÁN SỬA ĐỔI TRƯỚC KHI KÝ"
        else:
            return "CẦN ĐÀM PHÁN THỎA THUẬN LẠI MỘT SỐ ĐIỀU KHOẢN"

    def _build_system_prompt(self) -> str:
        return """Bạn là Luật sư cao cấp kiêm Chuyên gia đàm phán hợp đồng thuê nhà tại Việt Nam.

Nhiệm vụ của bạn là nhận danh sách các rủi ro (RiskItem) do Agent 2 phát hiện từ văn bản hợp đồng thuê nhà, kết hợp với Metadata của hợp đồng để:
1. SOẠN THẢO ĐIỀU KHOẢN SỬA ĐỔI (proposed_clause):
   - Chuẩn mực, văn phong pháp lý rõ ràng, bảo vệ quyền lợi hợp pháp của người thuê.
   - Dung hòa lợi ích của cả hai bên, bám sát các mẫu chuẩn của Nhà nước (Nghị định 96/2024/NĐ-CP, BLDS 2015, Luật Nhà ở 2023).
2. GẮN CĂN CỨ PHÁP LÝ CHẶT CHẼ (statutory_citation & reference_url):
   - Trích dẫn điều luật chính xác làm căn cứ pháp lý vững chắc (ví dụ: 'Khoản 2 Điều 132 Luật Nhà ở 2023', 'Khoản 2 Điều 328 BLDS 2015').
   - Kèm theo link tra cứu trên Cơ sở dữ liệu quốc gia về văn bản pháp luật vbpl.vn.
3. SOẠN KỊCH BẢN ĐÀM PHÁN (negotiation_script):
   - Lời thoại mẫu dành cho người thuê nhắn tin hoặc trao đổi trực tiếp với chủ nhà.
   - Văn phong: Lịch sự, tôn trọng, cầu thị, xưng hô phù hợp theo tên chủ nhà (nếu có trong Metadata).
   - Đưa ra lý lẽ pháp luật khéo léo để chủ nhà thấy việc sửa là hợp lý và đúng quy định pháp luật.
4. PHƯƠNG ÁN NHƯỢNG BỘ DỰ PHÒNG (compromise_option):
   - Đưa ra giải pháp bậc 2 nếu chủ nhà kiên quyết từ chối phương án tối ưu.

QUY TẮC BẮT BUỘC:
- Mọi đề xuất khởi tạo đều có hitl_status = 'PENDING_REVIEW'.
- Trả về DUY NHẤT một chuỗi JSON hợp lệ khớp với ContractReviewPackage schema.
"""

    def generate_review_package(
        self,
        contract_text: str,
        risk_analysis: RiskAnalysisResult,
        metadata: Optional[ContractMetadata] = None
    ) -> ContractReviewPackage:
        """
        Tổng hợp toàn bộ quá trình rà soát, sinh đề xuất sửa đổi (Redlines), 
        gắn Citation, kịch bản đàm phán và chuẩn bị cho vòng duyệt HITL.
        """
        red_count = risk_analysis.red_risks_count
        yellow_count = risk_analysis.yellow_risks_count
        safety_score = self._calculate_safety_score(red_count, yellow_count)
        verdict = self._determine_verdict(red_count, yellow_count, safety_score)

        # Trường hợp hợp đồng an toàn (Clean Contract)
        if risk_analysis.is_safe or not risk_analysis.risks:
            return ContractReviewPackage(
                executive_summary=(
                    "Hợp đồng thuê nhà đã được rà soát đối chiếu toàn diện với các quy định pháp luật hiện hành. "
                    "Các điều khoản rõ ràng, bình đẳng, không phát hiện điều khoản vi phạm điều cấm hoặc bất lợi nghiêm trọng."
                ),
                verdict=verdict,
                safety_score=10.0,
                total_risks_found=0,
                proposals=[],
                is_hitl_completed=True,
                final_contract_text=contract_text
            )

        # Nếu có client LLM, dùng model để sinh nội dung chuyên sâu và cá nhân hóa
        if self.client:
            try:
                review_package = self._generate_with_llm(
                    contract_text=contract_text,
                    risk_analysis=risk_analysis,
                    metadata=metadata,
                    safety_score=safety_score,
                    verdict=verdict
                )
                return review_package
            except Exception as e:
                # Nếu LLM gặp sự cố, tự động fallback sang cơ chế Rule-based an toàn
                print(f"[ProposalAgent Warning] LLM generation failed ({e}), switching to robust rule-based fallback.")

        # Fallback tạo đề xuất dựa trên Bộ quy tắc đóng kín (Rule-based Fallback)
        return self._generate_rule_based(
            contract_text=contract_text,
            risk_analysis=risk_analysis,
            metadata=metadata,
            safety_score=safety_score,
            verdict=verdict
        )

    def _generate_with_llm(
        self,
        contract_text: str,
        risk_analysis: RiskAnalysisResult,
        metadata: Optional[ContractMetadata],
        safety_score: float,
        verdict: str
    ) -> ContractReviewPackage:
        """Dùng LLM sinh đề xuất sửa đổi chuyên sâu và kịch bản đàm phán."""
        system_prompt = self._build_system_prompt()

        risks_payload = [r.model_dump() for r in risk_analysis.risks]
        metadata_payload = metadata.model_dump() if metadata else {}

        schema_json = json.dumps(ContractReviewPackage.model_json_schema(), ensure_ascii=False)
        user_content = {
            "instruction": "Hãy lập hồ sơ đánh giá và đề xuất sửa đổi hợp đồng thuê nhà đúng theo JSON Schema sau:",
            "json_schema": schema_json,
            "safety_score_calculated": safety_score,
            "verdict_calculated": verdict,
            "metadata": metadata_payload,
            "risks_detected": risks_payload,
            "contract_excerpt": contract_text[:2500]
        }

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        raw_json = response.choices[0].message.content.strip()
        if raw_json.startswith("```"):
            raw_json = re.sub(r"^```(?:json)?\n?", "", raw_json)
            raw_json = re.sub(r"\n?```$", "", raw_json)

        package_dict = json.loads(raw_json)

        # Mở bọc (Unwrap) nếu model gói trong key lồng nhau
        for wrapper_key in ["contract_review_package", "package", "data", "result"]:
            if wrapper_key in package_dict and isinstance(package_dict[wrapper_key], dict):
                package_dict = package_dict[wrapper_key]
                break

        # Đảm bảo các trường tính toán đồng bộ
        package_dict["safety_score"] = safety_score
        package_dict["verdict"] = verdict
        package_dict["total_risks_found"] = len(risk_analysis.risks)
        package_dict["is_hitl_completed"] = False
        package_dict["final_contract_text"] = None

        # Bổ khuyết các trường nếu LLM bỏ sót
        proposals_list = []
        for idx, p_dict in enumerate(package_dict.get("proposals", []), 1):
            if "proposal_id" not in p_dict or not p_dict["proposal_id"]:
                p_dict["proposal_id"] = f"PROP_{idx:03d}"
            
            # Map citation và link từ rules_map nếu thiếu
            r_id = p_dict.get("rule_id", "")
            if r_id in self.rules_map:
                ref_rule = self.rules_map[r_id]
                if not p_dict.get("statutory_citation"):
                    p_dict["statutory_citation"] = ref_rule.get("statutory_citation", "")
                if not p_dict.get("reference_url"):
                    p_dict["reference_url"] = ref_rule.get("reference_url", "")

            p_dict["hitl_status"] = "PENDING_REVIEW"
            proposals_list.append(RedlineProposal.model_validate(p_dict))

        package_dict["proposals"] = [p.model_dump() for p in proposals_list]
        return ContractReviewPackage.model_validate(package_dict)

    def _generate_rule_based(
        self,
        contract_text: str,
        risk_analysis: RiskAnalysisResult,
        metadata: Optional[ContractMetadata],
        safety_score: float,
        verdict: str
    ) -> ContractReviewPackage:
        """Cơ chế Fallback: Tạo đề xuất sửa đổi trực tiếp từ Bộ quy tắc luật đóng kín."""
        lessor_name = (metadata.lessor_name if metadata and metadata.lessor_name else "Bên A / Chủ nhà")
        
        proposals = []
        for idx, risk in enumerate(risk_analysis.risks, 1):
            rule_info = self.rules_map.get(risk.rule_id, {})
            
            suggested_clause = (
                rule_info.get("suggested_clause") 
                or risk.suggested_action 
                or "Hai bên thỏa thuận điều chỉnh điều khoản này theo quy định của Bộ luật Dân sự và Luật Nhà ở."
            )
            
            citation = (
                risk.statutory_citation 
                or rule_info.get("statutory_citation") 
                or risk.legal_basis
            )
            
            ref_url = (
                risk.reference_url 
                or rule_info.get("reference_url") 
                or "https://vbpl.vn/"
            )

            # Tạo kịch bản đàm phán lịch sự
            negotiation_script = (
                f"Dạ em chào anh/chị {lessor_name}. Em đã đọc kỹ dự thảo hợp đồng và rất có thiện chí thuê nhà lâu dài. "
                f"Tại {risk.related_article or 'điều khoản liên quan'}, em thấy có nội dung '{risk.original_clause[:80]}...'. "
                f"Quy định này hơi khắt khe và chưa hoàn toàn phù hợp với {citation}. "
                f"Em xin phép đề xuất hai bên sửa lại như sau: '{suggested_clause}'. "
                f"Phương án này vừa đúng quy định pháp luật vừa đảm bảo quyền lợi hài hòa cho cả hai bên. "
                f"Mong anh/chị xem xét và tạo điều kiện giúp em ạ!"
            )

            compromise_option = (
                f"Nếu Bên A lo lắng rủi ro phát sinh, Bên B đồng ý hỗ trợ thông báo sớm hơn "
                f"hoặc hỗ trợ chi phí tìm người thuê thay thế để Bên A không bị gián đoạn nguồn thu."
            )

            proposal = RedlineProposal(
                proposal_id=f"PROP_{idx:03d}",
                rule_id=risk.rule_id,
                rule_name=risk.rule_name,
                risk_level=risk.risk_level,
                related_article=risk.related_article,
                original_clause=risk.original_clause,
                proposed_clause=suggested_clause,
                statutory_citation=citation,
                reference_url=ref_url,
                negotiation_script=negotiation_script,
                compromise_option=compromise_option,
                hitl_status="PENDING_REVIEW",
                user_custom_clause=None,
                user_notes=None,
                final_clause=None
            )
            proposals.append(proposal)

        executive_summary = (
            f"Hợp đồng phát hiện tổng cộng {len(proposals)} điều khoản tiềm ẩn rủi ro "
            f"({risk_analysis.red_risks_count} rủi ro mức Đỏ vi phạm luật cấm, "
            f"{risk_analysis.yellow_risks_count} rủi ro mức Vàng bất lợi thương mại). "
            f"Hệ thống đã chuẩn bị đầy đủ căn cứ pháp lý (Statutory Citation) và điều khoản thay thế chuẩn mực. "
            f"Người thuê cần tiến hành kiểm duyệt (HITL) và đàm phán trước khi ký kết."
        )

        return ContractReviewPackage(
            executive_summary=executive_summary,
            verdict=verdict,
            safety_score=safety_score,
            total_risks_found=len(proposals),
            proposals=proposals,
            is_hitl_completed=False,
            final_contract_text=None
        )
