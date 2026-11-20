from typing import List, Dict, Tuple
from .legal_kb import LegalRule
from .sparse_bm25 import SparseBM25Retriever
from .dense_retriever import DenseRetriever

class HybridLegalReranker:
    """
    Tầng 3: Reranker kết hợp Hybrid Search (Reciprocal Rank Fusion - RRF).
    Hợp nhất bảng xếp hạng từ BM25 (từ vựng chính xác) và Dense Retriever (ngữ nghĩa sâu).
    
    Công thức RRF:
    RRF_Score(d) = (1 / (k + rank_sparse(d))) + (1 / (k + rank_dense(d)))
    với hằng số làm mượt k = 60 theo tiêu chuẩn IR quốc tế.
    """
    def __init__(self, rules: List[LegalRule], rrf_k: int = 60):
        self.rules = rules
        self.rrf_k = rrf_k
        self.sparse_retriever = SparseBM25Retriever(rules)
        self.dense_retriever = DenseRetriever(rules)

    def retrieve_and_rerank(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Thực hiện tìm kiếm lai và tái xếp hạng:
        Trả về danh sách Top-K quy tắc luật liên quan nhất cho một điều khoản hợp đồng.
        """
        sparse_hits = self.sparse_retriever.retrieve(query, top_k=top_k * 2)
        dense_hits = self.dense_retriever.retrieve(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        rule_map: Dict[str, LegalRule] = {}

        for rank, (rule, _) in enumerate(sparse_hits, 1):
            rrf_scores[rule.rule_id] = rrf_scores.get(rule.rule_id, 0.0) + (1.0 / (self.rrf_k + rank))
            rule_map[rule.rule_id] = rule

        for rank, (rule, _) in enumerate(dense_hits, 1):
            rrf_scores[rule.rule_id] = rrf_scores.get(rule.rule_id, 0.0) + (1.0 / (self.rrf_k + rank))
            rule_map[rule.rule_id] = rule

        # Sắp xếp theo RRF Score giảm dần
        sorted_rule_ids = sorted(rrf_scores.keys(), key=lambda rid: rrf_scores[rid], reverse=True)

        results = []
        for rid in sorted_rule_ids[:top_k]:
            rule = rule_map[rid]
            results.append({
                "rule": rule,
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "legal_basis": rule.legal_basis,
                "statutory_citation": rule.statutory_citation,
                "risk_level": rule.risk_level,
                "suggested_clause": rule.suggested_clause,
                "score": round(rrf_scores[rid], 5)
            })

        return results

