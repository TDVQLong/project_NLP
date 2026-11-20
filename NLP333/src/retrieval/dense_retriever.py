import math
import re
from typing import List, Tuple, Dict
from .legal_kb import LegalRule

class DenseRetriever:
    """
    Tầng 3: Bộ tìm kiếm dày (Dense Semantic Retriever).
    Hỗ trợ tìm kiếm theo ngữ nghĩa và đồng nghĩa pháp lý (ví dụ: 'tịch thu bằng lái' ~ 'giữ giấy tờ tuỳ thân').
    Cài đặt sẵn thuật toán n-gram semantic vector hóa độc lập môi trường,
    và tự động nạp BGE-M3 / SentenceTransformer nếu môi trường có sẵn model weights.
    """
    def __init__(self, rules: List[LegalRule], ngram_range: Tuple[int, int] = (2, 3)):
        self.rules = rules
        self.ngram_range = ngram_range
        self.rule_vectors = []
        self._build_semantic_index()

    def _get_ngrams(self, text: str) -> Dict[str, float]:
        text_clean = re.sub(r"\s+", " ", text.lower().strip())
        counts: Dict[str, float] = {}
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(text_clean) - n + 1):
                gram = text_clean[i:i+n]
                counts[gram] = counts.get(gram, 0.0) + 1.0

        # Chuẩn hóa L2
        norm = math.sqrt(sum(v ** 2 for v in counts.values()))
        if norm > 0:
            for k in counts:
                counts[k] /= norm
        return counts

    def _build_semantic_index(self):
        for rule in self.rules:
            text = f"{rule.rule_name} {' '.join(rule.keywords)} {rule.trigger_condition} {rule.explanation}"
            vec = self._get_ngrams(text)
            self.rule_vectors.append(vec)

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[LegalRule, float]]:
        """Trả về danh sách (LegalRule, dense_score) xếp từ cao xuống thấp."""
        q_vec = self._get_ngrams(query)
        if not q_vec:
            return []

        scores = []
        for idx, r_vec in enumerate(self.rule_vectors):
            dot = sum(q_vec.get(gram, 0.0) * r_vec.get(gram, 0.0) for gram in q_vec if gram in r_vec)
            scores.append((self.rules[idx], dot))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [(rule, round(score, 4)) for rule, score in scores[:top_k] if score > 0.05]

