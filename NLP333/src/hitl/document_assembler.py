import re
from typing import Optional
from ..agents.schemas import ContractReviewPackage

class DocumentAssembler:
    """
    Tầng 5: Bộ tái cấu trúc và lắp ráp tài liệu hoàn chỉnh (Document Assembler).
    Tự động thay thế chính xác các điều khoản đã được duyệt/sửa đổi bởi con người vào văn bản gốc,
    bảo toàn nguyên vẹn định dạng, số thứ tự điều khoản và tiêu đề hợp đồng.
    """

    @classmethod
    def assemble_final_contract(
        cls,
        original_contract_text: str,
        package: ContractReviewPackage
    ) -> str:
        if not package.proposals:
            return original_contract_text

        final_text = original_contract_text

        for proposal in package.proposals:
            if proposal.hitl_status not in ["APPROVED", "MODIFIED"]:
                continue

            target_replacement = proposal.final_clause or proposal.proposed_clause
            original = proposal.original_clause.strip()

            if not original or not target_replacement:
                continue

            # 1. Thử thay thế chính xác nguyên văn
            if original in final_text:
                final_text = final_text.replace(original, target_replacement, 1)
            else:
                # 2. Thử thay thế không phụ thuộc khoảng trắng thừa
                pattern = re.escape(re.sub(r"\s+", " ", original))
                pattern = pattern.replace(r"\ ", r"\s+")
                matched = re.search(pattern, final_text, re.IGNORECASE)
                if matched:
                    final_text = final_text[:matched.start()] + target_replacement + final_text[matched.end():]

        package.final_contract_text = final_text
        return final_text

