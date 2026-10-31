import re
from typing import Optional, List, Dict, Any, Tuple
from src.agents.schemas import RedlineProposal, ContractReviewPackage

class HITLController:
    """
    Bộ điều phối Human-in-the-Loop (HITL):
    Cho phép người dùng trực tiếp kiểm soát, phê duyệt, chỉnh sửa hoặc từ chối các đề xuất sửa đổi
    trước khi hệ thống tự động tái cấu trúc và xuất ra bản hợp đồng hoàn thiện.
    """

    VALID_ACTIONS = {"APPROVE", "MODIFY", "REJECT"}

    @classmethod
    def review_proposal(
        cls,
        package: ContractReviewPackage,
        proposal_id: str,
        action: str,
        custom_clause: Optional[str] = None,
        user_notes: Optional[str] = None
    ) -> RedlineProposal:
        """
        Xử lý quyết định của người dùng đối với một đề xuất cụ thể.
        
        Args:
            package: Đối tượng ContractReviewPackage chứa danh sách đề xuất.
            proposal_id: Mã đề xuất (ví dụ: 'PROP_001').
            action: Hành động của con người ('APPROVE', 'MODIFY', 'REJECT').
            custom_clause: Câu văn do người dùng tự gõ lại (bắt buộc khi action='MODIFY').
            user_notes: Ghi chú cá nhân của người dùng.
        """
        action_map = {
            "APPROVE": "APPROVED",
            "APPROVED": "APPROVED",
            "MODIFY": "MODIFIED",
            "MODIFIED": "MODIFIED",
            "REJECT": "REJECTED",
            "REJECTED": "REJECTED"
        }
        action = action.upper().strip()
        if action not in action_map:
            raise ValueError(f"Hành động không hợp lệ: '{action}'. Chỉ chấp nhận: APPROVE, MODIFY, REJECT")

        normalized_status = action_map[action]

        target_prop = None
        for p in package.proposals:
            if p.proposal_id == proposal_id:
                target_prop = p
                break

        if not target_prop:
            raise KeyError(f"Không tìm thấy đề xuất có mã: {proposal_id}")

        target_prop.hitl_status = normalized_status
        target_prop.user_notes = user_notes

        if normalized_status == "APPROVED":
            # Con người đồng thuận sử dụng phương án do AI đề xuất
            target_prop.final_clause = target_prop.proposed_clause
            target_prop.user_custom_clause = None

        elif normalized_status == "MODIFIED":
            # Con người chủ động sửa lại câu từ theo thỏa thuận riêng
            if not custom_clause or not custom_clause.strip():
                raise ValueError("Khi chọn hành động 'MODIFY', bạn phải cung cấp nội dung custom_clause.")
            target_prop.user_custom_clause = custom_clause.strip()
            target_prop.final_clause = custom_clause.strip()

        elif normalized_status == "REJECTED":
            # Con người quyết định giữ nguyên điều khoản ban đầu của chủ nhà
            target_prop.final_clause = target_prop.original_clause
            target_prop.user_custom_clause = None

        # Kiểm tra xem toàn bộ các đề xuất đã được review hay chưa
        all_reviewed = all(p.hitl_status != "PENDING_REVIEW" for p in package.proposals)
        package.is_hitl_completed = all_reviewed

        return target_prop

    @classmethod
    def bulk_approve(cls, package: ContractReviewPackage) -> ContractReviewPackage:
        """
        Phê duyệt nhanh toàn bộ các đề xuất đang ở trạng thái PENDING_REVIEW.
        """
        for p in package.proposals:
            if p.hitl_status == "PENDING_REVIEW":
                p.hitl_status = "APPROVED"
                p.final_clause = p.proposed_clause

        package.is_hitl_completed = True
        return package

    @classmethod
    def assemble_final_contract(
        cls,
        original_contract_text: str,
        package: ContractReviewPackage
    ) -> str:
        """
        Thay thế chính xác các điều khoản đã được con người duyệt (APPROVED hoặc MODIFIED)
        vào văn bản hợp đồng ban đầu để tạo ra bản hợp đồng hoàn chỉnh sẵn sàng in/ký.
        """
        final_text = original_contract_text

        for p in package.proposals:
            # Chỉ thay thế nếu trạng thái là APPROVED hoặc MODIFIED và có sự thay đổi
            if p.hitl_status in ["APPROVED", "MODIFIED"] and p.final_clause:
                orig = p.original_clause.strip()
                replacement = p.final_clause.strip()

                if orig in final_text:
                    final_text = final_text.replace(orig, replacement)
                else:
                    # Thuật toán thay thế mềm (Fuzzy/Whitespace-insensitive replacement)
                    # Giúp xử lý các trường hợp lệch dấu cách thừa, thụt dòng hoặc xuống dòng \r\n
                    orig_pattern = re.escape(orig)
                    orig_pattern = re.sub(r"\\\s+", r"\\s+", orig_pattern)
                    match = re.search(orig_pattern, final_text)
                    if match:
                        start, end = match.span()
                        final_text = final_text[:start] + replacement + final_text[end:]

        package.final_contract_text = final_text
        return final_text

    @classmethod
    def calculate_post_hitl_safety_score(cls, package: ContractReviewPackage) -> float:
        """
        Tính toán lại thang điểm an toàn hợp đồng sau khi con người đã duyệt:
        - Những điều khoản rủi ro Đỏ/Vàng đã được APPROVED hoặc MODIFIED (sửa thành an toàn) sẽ được xóa trừ điểm.
        - Những điều khoản bị REJECT (người dùng cố tình giữ nguyên rủi ro ban đầu) vẫn tiếp tục bị trừ điểm.
        """
        penalty = 0.0
        for p in package.proposals:
            if p.hitl_status == "REJECTED":
                if p.risk_level.upper() == "RED":
                    penalty += 2.5
                else:
                    penalty += 1.0

        post_score = max(1.0, min(10.0, round(10.0 - penalty, 1)))
        return post_score

    @classmethod
    def generate_diff_report(cls, package: ContractReviewPackage) -> str:
        """
        Tạo báo cáo chi tiết so sánh Đối chiếu Trước & Sau (Before vs After Redlining)
        kèm Trích dẫn Pháp luật (Citation) và trạng thái duyệt HITL dạng Markdown.
        """
        lines = [
            "# BẢNG ĐỐI CHIẾU ĐIỀU KHOẢN TRƯỚC VÀ SAU RÀ SOÁT (REDLINE DIFF REPORT)",
            f"- **Phán quyết ban đầu:** {package.verdict}",
            f"- **Điểm an toàn ban đầu:** {package.safety_score}/10.0",
            f"- **Điểm an toàn sau khi duyệt HITL:** {cls.calculate_post_hitl_safety_score(package)}/10.0",
            f"- **Tổng số đề xuất:** {len(package.proposals)}",
            "",
            "---",
            ""
        ]

        for p in package.proposals:
            status_badge = {
                "APPROVED": "✅ ĐÃ PHÊ DUYỆT (Áp dụng đề xuất AI)",
                "MODIFIED": "✏️ ĐÃ CHỈNH SỬA (Theo ý người dùng)",
                "REJECTED": "❌ BÁC BỎ (Giữ nguyên gốc chủ nhà)",
                "PENDING_REVIEW": "⏳ CHỜ DUYỆT (Pending Review)"
            }.get(p.hitl_status, p.hitl_status)

            lines.append(f"### Đề xuất {p.proposal_id}: {p.rule_name} ({p.risk_level})")
            if p.related_article:
                lines.append(f"**Vị trí trong hợp đồng:** {p.related_article}")
            lines.append(f"**Trạng thái HITL:** {status_badge}")
            lines.append(f"**Căn cứ pháp lý (Citation):** {p.statutory_citation}")
            if p.reference_url:
                lines.append(f"**Tra cứu vbpl.vn:** [{p.reference_url}]({p.reference_url})")
            
            lines.append("")
            lines.append("```diff")
            lines.append(f"- [GỐC CỦA CHỦ NHÀ]: {p.original_clause}")
            if p.hitl_status == "MODIFIED":
                lines.append(f"+ [NGƯỜI DÙNG TỰ SỬA]: {p.final_clause}")
            elif p.hitl_status == "APPROVED":
                lines.append(f"+ [ĐỀ XUẤT CỦA AI]: {p.final_clause}")
            elif p.hitl_status == "REJECTED":
                lines.append(f"  [GIỮ NGUYÊN GỐC]: {p.final_clause}")
            else:
                lines.append(f"+ [ĐỀ XUẤT THAY THẾ]: {p.proposed_clause}")
            lines.append("```")

            lines.append("")
            lines.append(f"💬 **Kịch bản đàm phán gửi chủ nhà:**")
            lines.append(f"> *\"{p.negotiation_script}\"*")
            
            if p.compromise_option:
                lines.append("")
                lines.append(f"🛡️ **Phương án nhượng bộ dự phòng (Bậc 2):** {p.compromise_option}")

            lines.append("\n---\n")

        return "\n".join(lines)
