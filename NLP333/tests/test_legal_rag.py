import unittest
from pathlib import Path
from src.retrieval.legal_kb import LegalKnowledgeBase
from src.retrieval.sparse_bm25 import SparseBM25Retriever
from src.retrieval.reranker import HybridLegalReranker

class TestLegalRAG(unittest.TestCase):
    def setUp(self):
        # Nạp KB trực tiếp từ thư mục data
        data_dir = Path(__file__).resolve().parent.parent / "data"
        self.kb = LegalKnowledgeBase(contract_type="rental", data_dir=str(data_dir))

    def test_kb_load_rules(self):
        rules = self.kb.get_all_rules()
        self.assertGreaterEqual(len(rules), 28)

    def test_sparse_bm25_retrieval(self):
        retriever = SparseBM25Retriever(self.kb.get_all_rules())
        results = retriever.retrieve("chủ nhà tự ý vào phòng kiểm tra không báo trước", top_k=3)
        self.assertGreater(len(results), 0)
        top_rule = results[0][0]
        self.assertIn("ENTRY", top_rule.rule_id)

    def test_hybrid_reranker(self):
        reranker = HybridLegalReranker(self.kb.get_all_rules())
        results = reranker.retrieve_and_rerank("tiền đặt cọc và trừ tiền cọc vô lý", top_k=2)
        self.assertEqual(len(results), 2)
        self.assertIn("rule_id", results[0])

if __name__ == "__main__":
    unittest.main()

