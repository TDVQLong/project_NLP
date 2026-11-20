import math
import re
from typing import List, Dict, Optional

class BaselineAligner:
    """
    Tầng 2: So khớp Cosine Similarity giữa các điều khoản của người dùng (C_i)
    với Hợp đồng Mẫu Chuẩn Nhà nước (Canonical Baseline B_j).
    
    Mục đích:
    - Tìm xem Điều C_i trong hợp đồng người dùng ứng với Điều B_j nào trong bản chuẩn.
    - Phát hiện độ lệch ngữ nghĩa và biến tướng so với chuẩn mực pháp lý.
    """
    def __init__(self, canonical_clauses: Optional[List[Dict[str, str]]] = None):
        self.canonical_clauses = canonical_clauses or []

    def load_canonical_baseline(self, canonical_data: Dict):
        """Nạp dữ liệu bản chuẩn từ dictionary (ví dụ: sample_employment_canonical.json)."""
        if "clauses" in canonical_data:
            self.canonical_clauses = canonical_data["clauses"]
        elif isinstance(canonical_data, list):
            self.canonical_clauses = canonical_data

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        words = re.findall(r"\w+", text.lower())
        return words

    def _compute_cosine_similarity(self, text_a: str, text_b: str) -> float:
        """Tính Cosine Similarity dựa trên Vector Không Gian Từ (TF Vector)."""
        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)
        if not tokens_a or not tokens_b:
            return 0.0

        vocab = set(tokens_a).union(set(tokens_b))
        vec_a = {word: tokens_a.count(word) for word in vocab}
        vec_b = {word: tokens_b.count(word) for word in vocab}

        dot_product = sum(vec_a[w] * vec_b[w] for w in vocab)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def align_clause(self, user_clause_text: str, threshold: float = 0.25) -> Optional[Dict]:
        """
        Tìm điều khoản chuẩn có độ tương đồng Cosine cao nhất với điều khoản người dùng.
        """
        best_match = None
        highest_score = 0.0

        for b_clause in self.canonical_clauses:
            b_text = b_clause.get("content", "") or b_clause.get("raw_text", "")
            score = self._compute_cosine_similarity(user_clause_text, b_text)
            if score > highest_score:
                highest_score = score
                best_match = b_clause

        if best_match and highest_score >= threshold:
            return {
                "canonical_clause_id": best_match.get("clause_id", ""),
                "canonical_title": best_match.get("title", ""),
                "similarity_score": round(highest_score, 4),
                "canonical_text": best_match.get("content", "") or best_match.get("raw_text", "")
            }
        return None

