import unittest
from pathlib import Path
from src.ingestion.router import route_document
from src.segmentation.clause_segmenter import ClauseSegmenter
from src.retrieval.legal_kb import LegalKnowledgeBase
from src.retrieval.reranker import HybridLegalReranker
from src.agents.risk_analyzer_agent import RiskAnalyzerAgent
from src.agents.reflection_critic import ReflectionCritic
from src.agents.proposal_agent import ProposalAgent
from src.hitl.hitl_controller import HITLController
from src.hitl.document_assembler import DocumentAssembler

class TestFullPipeline(unittest.TestCase):
    def test_end_to_end_pipeline(self):
        sample_contract = (
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
            "HỢP ĐỒNG THUÊ PHÒNG TRỌ\n\n"
            "Điều 1: Tiền thuê phòng là 3.000.000 đ/tháng.\n"
            "Điều 2: Tiền đặt cọc là 3.000.000 đ.\n"
            "Điều 3: Bên A có quyền vào kiểm tra phòng bất cứ lúc nào mà không cần báo trước cho Bên B.\n"
        )

        # Tầng 1: Ingestion
        temp_file = Path("test_contract_e2e.txt")
        temp_file.write_text(sample_contract, encoding="utf-8")
        try:
            text = route_document(str(temp_file))
            self.assertIn("HỢP ĐỒNG THUÊ PHÒNG TRỌ", text)

            # Tầng 2: Segmentation
            segmenter = ClauseSegmenter()
            clauses = segmenter.segment(text)
            self.assertEqual(len(clauses), 3)

            # Tầng 3: Retrieval RAG
            data_dir = Path(__file__).resolve().parent.parent / "data"
            kb = LegalKnowledgeBase(contract_type="rental", data_dir=str(data_dir))
            reranker = HybridLegalReranker(kb.get_all_rules())
            rag_hits = reranker.retrieve_and_rerank(clauses[2]["raw_text"], top_k=2)
            self.assertGreater(len(rag_hits), 0)

            # Tầng 4: Agents & NLI
            analyzer = RiskAnalyzerAgent(contract_type="rental")
            raw_risk = analyzer._rule_based_fallback_analyze(text)
            
            critic = ReflectionCritic()
            refined_risk = critic.critique_and_refine(text, raw_risk)
            
            proposer = ProposalAgent(contract_type="rental")
            package = proposer.formulate_proposals(text, refined_risk)
            self.assertGreater(len(package.proposals), 0)

            # Tầng 5: HITL & Assembly
            # Giả lập người dùng phê duyệt đề xuất đầu tiên
            first_prop_id = package.proposals[0].proposal_id
            HITLController.review_proposal(package, first_prop_id, "APPROVE")
            
            final_text = DocumentAssembler.assemble_final_contract(text, package)
            self.assertIsNotNone(final_text)
            # Điều khoản gốc đã được thay bằng điều khoản sửa đổi an toàn
            self.assertNotEqual(final_text, text)
        finally:
            if temp_file.exists():
                temp_file.unlink()

if __name__ == "__main__":
    unittest.main()

