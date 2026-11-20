import unittest
from pathlib import Path
from src.agents.risk_analyzer_agent import RiskAnalyzerAgent
from src.agents.reflection_critic import ReflectionCritic
from src.agents.schemas import RiskAnalysisResult, RiskItem

class TestNLIReasoning(unittest.TestCase):
    def test_rule_based_risk_detection(self):
        analyzer = RiskAnalyzerAgent(contract_type="rental")
        test_clause = "Bên A có quyền vào kiểm tra phòng trọ bất cứ lúc nào mà không cần báo trước cho Bên B."
        res = analyzer._rule_based_fallback_analyze(test_clause)
        self.assertFalse(res.is_safe)
        self.assertGreater(res.total_risks, 0)
        
        # Verify reflection critic keeps real verbatim clause
        critic = ReflectionCritic()
        refined = critic.critique_and_refine(test_clause, res)
        self.assertGreater(refined.total_risks, 0)

    def test_reflection_critic_hallucination_removal(self):
        contract_text = "Hợp đồng thuê nhà chuẩn mực, hai bên hợp tác vui vẻ."
        fake_risk = RiskItem(
            rule_id="RULE_TEST",
            rule_name="Test Rule",
            category="Test",
            risk_level="RED",
            original_clause="Bên A tịch thu xe máy và toàn bộ tài sản Bên B",
            legal_basis="BLDS",
            explanation="Hallucination test"
        )
        fake_result = RiskAnalysisResult(
            is_safe=False,
            total_risks=1,
            red_risks_count=1,
            yellow_risks_count=0,
            risks=[fake_risk],
            overall_assessment="Testing"
        )
        critic = ReflectionCritic()
        refined = critic.critique_and_refine(contract_text, fake_result)
        # Báo động giả bị loại bỏ
        self.assertEqual(refined.total_risks, 0)
        self.assertTrue(refined.is_safe)

if __name__ == "__main__":
    unittest.main()

