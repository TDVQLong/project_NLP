from typing import Optional, List, Dict
from ..agents.schemas import RedlineProposal, ContractReviewPackage

class HITLController:
    """
    Tầng 5: Bộ điều phối Human-In-The-Loop (HITL).
    Quản lý luồng kiểm duyệt của người dùng đối với các đề xuất Redline:
    - APPROVE: Phê duyệt câu sửa đổi chuẩn mực của AI
    - MODIFY: Người dùng tự nhập lại câu chữ theo ý muốn
    - REJECT: Giữ nguyên câu chữ ban đầu
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
            raise ValueError(f"Hành động không hợp lệ: '{action}'. Hỗ trợ: APPROVE, MODIFY, REJECT")

        normalized_status = action_map[action]
        target_prop = None
        for p in package.proposals:
            if p.proposal_id == proposal_id:
                target_prop = p
                break

        if not target_prop:
            raise KeyError(f"Không tìm thấy đề xuất: {proposal_id}")

        target_prop.hitl_status = normalized_status
        target_prop.user_notes = user_notes

        if normalized_status == "APPROVED":
            target_prop.final_clause = target_prop.proposed_clause
            target_prop.user_custom_clause = None
        elif normalized_status == "MODIFIED":
            if not custom_clause or not custom_clause.strip():
                raise ValueError("Cần cung cấp nội dung custom_clause khi chọn MODIFY.")
            target_prop.user_custom_clause = custom_clause.strip()
            target_prop.final_clause = custom_clause.strip()
        elif normalized_status == "REJECTED":
            target_prop.final_clause = target_prop.original_clause
            target_prop.user_custom_clause = None

        all_reviewed = all(p.hitl_status not in ("PENDING", "PENDING_REVIEW") for p in package.proposals)
        package.is_hitl_completed = all_reviewed
        return target_prop

    @classmethod
    def bulk_approve(cls, package: ContractReviewPackage) -> ContractReviewPackage:
        """Phê duyệt nhanh toàn bộ đề xuất còn chờ."""
        for p in package.proposals:
            if p.hitl_status in ("PENDING", "PENDING_REVIEW"):
                p.hitl_status = "APPROVED"
                p.final_clause = p.proposed_clause
        package.is_hitl_completed = True
        return package

