import unittest
import pandas as pd
from src.explainability.explainer import Explainer
from src.fusion.risk_models import RiskAssessment, RiskLevel

class TestExplainer(unittest.TestCase):

    def setUp(self):
        self.explainer = Explainer()
        self.transaction_id = "txn_123"
        self.features_df = pd.DataFrame(
            {"amount": [10000.0]}, 
            index=["txn_123"]
        )
        
        self.risk_assessment = RiskAssessment(
            transaction_id="txn_123",
            customer_id="cust_001",
            overall_risk_score=85.5,
            confidence_score=0.9,
            risk_level=RiskLevel.CRITICAL,
            engine_scores={"Rule": 100.0, "ML": 70.0},
            engine_weights={"Rule": 0.5, "ML": 0.5},
            supporting_evidence={
                "Behaviour": ["High velocity"],
                "Rule": ["Structuring detected"]
            },
            triggered_rules=["R001"],
            triggered_patterns=["P002"],
            top_reasons=["Structuring detected", "High velocity"],
            risk_breakdown={"Rule": "Triggered R001"}
        )
        
        self.engine_results = {
            self.transaction_id: self.risk_assessment
        }

    def test_explain_generates_correct_narrative(self):
        features = self.features_df.loc[self.transaction_id]
        explanation = self.explainer.explain(self.transaction_id, self.engine_results, features)
        
        self.assertEqual(explanation.transaction_id, self.transaction_id)
        self.assertEqual(explanation.risk_score, 85.5)
        self.assertIn("CRITICAL risk level (Score: 85.5)", explanation.narrative)
        self.assertIn("Primary drivers: Structuring detected, High velocity", explanation.narrative)
        self.assertIn("Triggered 1 hard rules", explanation.narrative)
        self.assertIn("Matched 1 known AML typologies", explanation.narrative)
        self.assertIn("Found 1 behavioural anomalies", explanation.narrative)

    def test_explain_extracts_contributing_factors(self):
        features = self.features_df.loc[self.transaction_id]
        explanation = self.explainer.explain(self.transaction_id, self.engine_results, features)
        
        factors = explanation.contributing_factors
        # 2 from engines, 1 from behaviour findings
        self.assertTrue(len(factors) >= 3)
        
        rule_factor = next(f for f in factors if f["factor"] == "Rule")
        self.assertEqual(rule_factor["score"], 100.0)
        self.assertEqual(rule_factor["weight"], 0.5)
        self.assertEqual(rule_factor["breakdown"], "Triggered R001")
        
        behaviour_factor = next(f for f in factors if f["factor"] == "Behaviour Findings")
        self.assertIn("High velocity", behaviour_factor["details"])

    def test_explain_extracts_rules_and_patterns(self):
        features = self.features_df.loc[self.transaction_id]
        explanation = self.explainer.explain(self.transaction_id, self.engine_results, features)
        
        self.assertEqual(explanation.triggered_rules, ["R001"])
        self.assertEqual(explanation.matched_patterns, ["P002"])

    def test_explain_batch_processes_all_transactions(self):
        explanations = self.explainer.explain_batch(
            transaction_ids=[self.transaction_id], 
            engine_results=self.engine_results, 
            features_df=self.features_df
        )
        
        self.assertEqual(len(explanations), 1)
        self.assertEqual(explanations[0].transaction_id, self.transaction_id)
        self.assertEqual(explanations[0].risk_score, 85.5)

    def test_explain_handles_missing_assessment(self):
        explanation = self.explainer.explain("txn_999", self.engine_results, pd.Series(dtype=float))
        
        self.assertEqual(explanation.transaction_id, "txn_999")
        self.assertEqual(explanation.risk_score, 0.0)
        self.assertEqual(explanation.narrative, "No assessment data available for explanation.")

if __name__ == '__main__':
    unittest.main()
