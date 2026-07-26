# pyrefly: ignore [missing-import]
import pytest
import pandas as pd

from src.recommendation.recommender import Recommender, Recommendation
from src.constants.risk_levels import RecommendedAction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(**kwargs) -> dict:
    defaults = dict(
        transaction_id="TXN001",
        customer_id="CUST001",
        overall_risk_score=85.0,
        risk_level="CRITICAL",
        confidence_score=0.91,
        triggered_rules=["R001", "R013"],
        triggered_patterns=["Structuring"],
        supporting_evidence={
            "Behaviour": ["High velocity"],
            "Statistical": ["Outlier amount"],
            "ML": ["AnomalyScore=0.95"],
        },
        top_reasons=["Structuring detected", "High velocity"],
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# Tests — recommend()
# ---------------------------------------------------------------------------

class TestRecommend:

    def setup_method(self):
        self.recommender = Recommender()

    def test_critical_risk_produces_sar_and_freeze(self):
        row = _make_row(overall_risk_score=90.0, risk_level="CRITICAL")
        recs = self.recommender.recommend(**row)

        titles = [r.title for r in recs]
        actions = [r.action for r in recs]

        assert RecommendedAction.FILE_SAR in actions
        assert RecommendedAction.FREEZE_ACCOUNT in actions
        assert "File Suspicious Activity Report" in titles

    def test_high_risk_produces_escalate(self):
        row = _make_row(
            overall_risk_score=55.0, risk_level="HIGH",
            triggered_patterns=[], supporting_evidence={},
        )
        recs = self.recommender.recommend(**row)

        actions = [r.action for r in recs]
        assert RecommendedAction.ESCALATE_TO_COMPLIANCE in actions

    def test_medium_risk_produces_request_documents(self):
        row = _make_row(
            overall_risk_score=35.0, risk_level="MEDIUM",
            triggered_patterns=[], supporting_evidence={},
        )
        recs = self.recommender.recommend(**row)

        actions = [r.action for r in recs]
        assert RecommendedAction.REQUEST_DOCUMENTS in actions

    def test_low_risk_produces_monitor(self):
        row = _make_row(
            overall_risk_score=10.0, risk_level="LOW",
            triggered_rules=[], triggered_patterns=[], supporting_evidence={},
            top_reasons=[],
        )
        recs = self.recommender.recommend(**row)

        assert len(recs) == 1
        assert recs[0].action == RecommendedAction.MONITOR_ACCOUNT

    def test_pattern_match_adds_kyc_refresh(self):
        row = _make_row(overall_risk_score=90.0, risk_level="CRITICAL")
        recs = self.recommender.recommend(**row)

        titles = [r.title for r in recs]
        assert "Refresh Customer KYC" in titles

    def test_stat_findings_add_history_review(self):
        row = _make_row(overall_risk_score=90.0, risk_level="CRITICAL")
        recs = self.recommender.recommend(**row)

        titles = [r.title for r in recs]
        assert "Review Historical Transactions" in titles

    def test_behaviour_findings_add_related_accounts(self):
        row = _make_row(overall_risk_score=90.0, risk_level="CRITICAL")
        recs = self.recommender.recommend(**row)

        titles = [r.title for r in recs]
        assert "Review Related Accounts" in titles

    def test_ml_findings_add_verify_funds(self):
        row = _make_row(overall_risk_score=90.0, risk_level="CRITICAL")
        recs = self.recommender.recommend(**row)

        titles = [r.title for r in recs]
        assert "Verify Source of Funds" in titles

    def test_recommendations_sorted_by_priority(self):
        row = _make_row(overall_risk_score=90.0, risk_level="CRITICAL")
        recs = self.recommender.recommend(**row)

        priorities = [r.priority for r in recs]
        assert priorities == sorted(priorities)

    def test_recommendation_fields_are_populated(self):
        row = _make_row(overall_risk_score=90.0, risk_level="CRITICAL")
        recs = self.recommender.recommend(**row)

        for rec in recs:
            assert isinstance(rec, Recommendation)
            assert rec.transaction_id == "TXN001"
            assert rec.title
            assert rec.description
            assert rec.reason
            assert rec.suggested_investigator_action


# ---------------------------------------------------------------------------
# Tests — recommend_batch()
# ---------------------------------------------------------------------------

class TestRecommendBatch:

    def setup_method(self):
        self.recommender = Recommender()

    def test_batch_returns_dict_keyed_by_transaction_id(self):
        df = pd.DataFrame([_make_row()])
        result = self.recommender.recommend_batch(df)

        assert "TXN001" in result
        assert isinstance(result["TXN001"], list)
        assert len(result["TXN001"]) > 0

    def test_batch_processes_multiple_transactions(self):
        rows = [
            _make_row(transaction_id="TXN001", risk_level="CRITICAL", overall_risk_score=90.0),
            _make_row(transaction_id="TXN002", risk_level="LOW", overall_risk_score=10.0,
                      triggered_rules=[], triggered_patterns=[], supporting_evidence={}, top_reasons=[]),
        ]
        df = pd.DataFrame(rows)
        result = self.recommender.recommend_batch(df)

        assert "TXN001" in result
        assert "TXN002" in result
        assert result["TXN001"][0].action == RecommendedAction.FILE_SAR
        assert result["TXN002"][0].action == RecommendedAction.MONITOR_ACCOUNT

    def test_batch_empty_dataframe_returns_empty_dict(self):
        result = self.recommender.recommend_batch(pd.DataFrame())
        assert result == {}

    def test_batch_invalid_input_returns_empty_dict(self):
        result = self.recommender.recommend_batch(None)
        assert result == {}
