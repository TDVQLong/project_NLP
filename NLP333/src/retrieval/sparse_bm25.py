import math
import re
from typing import List, Dict, Tuple
from .legal_kb import LegalRule

class SparseBM25Retriever:
    """
    Tầng 3: Bộ tìm kiếm thưa BM25 (Okapi BM25).
    Tối ưu cho việc tìm kiếm chính xác các từ khóa pháp lý (cọc, giữ bằng gốc, phạt vi phạm, thử việc).
    """
    def __init__(self, rules: List[LegalRule], k1: float = 1.5, b: float = 0.75):
        self.rules = rules
        self.k1 = k1
        self.b = b
        self.corpus_size = len(rules)
        self.doc_lengths = []
        self.avg_doc_len = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.tokenized_corpus: List[List[str]] = []

        self._build_index()

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def _build_index(self):
        total_length = 0
        for rule in self.rules:
            # Gộp các trường thông tin để làm văn bản chỉ mục
            doc_text = f"{rule.rule_name} {' '.join(rule.keywords)} {rule.legal_basis} {rule.trigger_condition} {rule.explanation}"
            tokens = self.tokenize(doc_text)
            self.tokenized_corpus.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_length += doc_len

            # Đếm tần suất xuất hiện trong tài liệu
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_doc_len = total_length / self.corpus_size if self.corpus_size > 0 else 1.0

        # Tính IDF theo công thức chuẩn Okapi
        for token, df in self.doc_freqs.items():
            self.idf[token] = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[LegalRule, float]]:
        """Trả về danh sách (LegalRule, bm25_score) xếp từ cao xuống thấp."""
        query_tokens = self.tokenize(query)
        scores = [0.0] * self.corpus_size

        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]

            for idx, doc_tokens in enumerate(self.tokenized_corpus):
                tf = doc_tokens.count(token)
                if tf > 0:
                    doc_len = self.doc_lengths[idx]
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    scores[idx] += idf_val * (numerator / denominator)

        # Kết hợp điểm thưởng nếu câu truy vấn chứa trực tiếp keyword của rule
        query_lower = query.lower()
        for idx, rule in enumerate(self.rules):
            for kw in rule.keywords:
                if kw.lower() in query_lower:
                    scores[idx] += 2.0

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked_indices[:top_k]:
            if scores[i] > 0.05:
                results.append((self.rules[i], round(scores[i], 4)))
        return results

