from typing import List, Dict

class OmissionDetector:
    """
    Tầng 2: Phát hiện các điều khoản bảo vệ người yếu thế bị cố tình lược bỏ (Omission Detection).
    
    Phương pháp:
    So sánh tập các điều khoản đã được map với Baseline Mẫu Chuẩn.
    Nếu một điều khoản bắt buộc (Mandatory Canonical Clause) không có bất kỳ điều nào trong hợp đồng
    người dùng map tới (hoặc Cosine Similarity < 0.2), đánh dấu là "Rủi ro thiếu sót / Omission Risk".
    """
    def __init__(self, canonical_clauses: List[Dict]):
        self.canonical_clauses = canonical_clauses

    def detect_omissions(self, aligned_results: List[Dict]) -> List[Dict]:
        """
        aligned_results: Danh sách kết quả trả về từ BaselineAligner cho từng điều khoản người dùng.
        """
        matched_canonical_ids = set()
        for res in aligned_results:
            if res and res.get("canonical_clause_id"):
                matched_canonical_ids.add(res["canonical_clause_id"])

        omissions = []
        for c in self.canonical_clauses:
            cid = c.get("clause_id")
            # Các điều khoản quan trọng bảo vệ bên yếu thế
            is_critical = c.get("is_mandatory", True)
            if cid not in matched_canonical_ids and is_critical:
                omissions.append({
                    "omitted_clause_id": cid,
                    "title": c.get("title", ""),
                    "reason": f"Hợp đồng không đề cập hoặc đã lược bỏ hoàn toàn điều khoản bảo vệ bắt buộc: '{c.get('title')}'.",
                    "legal_basis": c.get("legal_basis", "Quy định mẫu chuẩn của Nhà nước"),
                    "recommendation": f"Đề xuất bổ sung điều khoản về '{c.get('title')}' theo mẫu chuẩn để bảo vệ quyền lợi hợp pháp."
                })

        return omissions

