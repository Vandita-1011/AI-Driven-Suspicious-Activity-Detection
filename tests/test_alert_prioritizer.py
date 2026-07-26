# pyrefly: ignore [missing-import]
import pytest
import pandas as pd
from unittest.mock import patch

from src.alerts.alert_prioritizer import AlertPrioritizer, Alert
from src.constants.risk_levels import AlertPriority
from src.interfaces.base_explainer import Explanation
from src.recommendation.recommender import Recommendation
from src.constants.risk_levels import RecommendedAction


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_risk_row(**kwargs) -> dict:
    defaults = dict(
        transaction_id="TXN001",
        customer_id="CUST001",
        overall_risk_score=90.0,
        risk_level="CRITICAL",
        confidence_score=0.92,
        triggered_rules=["R001", "R013"],
        triggered_patterns=["Structuring"],
        top_reasons=["Structuring", "Large Amount"],
        supporting_evidence={"Behaviour": ["High velocity"]},
    )
    defaults.update(kwargs)
    return defaults


def _make_explanation(tid: str = "TXN001", score: float = 90.0) -> Explanation:
    return Explanation(
        transaction_id=tid,
        risk_score=score,
        narrative=f"Transaction {tid} classified as CRITICAL.",
        contributing_factors=[{"factor": "Rule", "score": 100.0}],
        triggered_rules=["R001"],
        matched_patterns=["Structuring"],
    )


def _make_recommendation(tid: str = "TXN001") -> Recommendation:
    return Recommendation(
        transaction_id=tid,
        title="File Suspicious Activity Report",
        description="Critical risk detected.",
        priority=1,
        reason="CRITICAL risk level.",
        action=RecommendedAction.FILE_SAR,
        suggested_investigator_action="Submit SAR within 24 hours.",
        triggered_by=["R001"],
    )


@pytest.fixture
def prioritizer():
    return AlertPrioritizer()


@pytest.fixture
def single_row_df():
    return pd.DataFrame([_make_risk_row()])


@pytest.fixture
def single_explanation():
    return [_make_explanation("TXN001")]


@pytest.fixture
def single_recommendation():
    return {"TXN001": [_make_recommendation("TXN001")]}


# ---------------------------------------------------------------------------
# Tests — prioritize() basic behaviour
# ---------------------------------------------------------------------------

class TestPrioritize:

    def test_returns_list_of_alerts(self, prioritizer, single_row_df, single_explanation, single_recommendation):
        alerts = prioritizer.prioritize(single_row_df, single_explanation, single_recommendation)
        assert isinstance(alerts, list)
        assert len(alerts) == 1
        assert isinstance(alerts[0], Alert)

    def test_empty_dataframe_returns_empty_list(self, prioritizer):
        alerts = prioritizer.prioritize(pd.DataFrame(), [], {})
        assert alerts == []

    def test_none_input_returns_empty_list(self, prioritizer):
        alerts = prioritizer.prioritize(None, [], {})
        assert alerts == []

    def test_alert_fields_populated(self, prioritizer, single_row_df, single_explanation, single_recommendation):
        alert = prioritizer.prioritize(single_row_df, single_explanation, single_recommendation)[0]

        assert alert.transaction_id == "TXN001"
        assert alert.customer_id == "CUST001"
        assert alert.fused_risk_score == 90.0
        assert alert.risk_level == "CRITICAL"
        assert alert.confidence_score == 0.92
        assert alert.status == "OPEN"
        assert alert.alert_id.startswith("ALT-")
        assert alert.narrative != ""
        assert alert.alert_title != ""
        assert alert.alert_summary != ""
        assert alert.investigator_action != ""
        assert alert.recommended_action != ""

    def test_critical_score_maps_to_p1(self, prioritizer, single_explanation, single_recommendation):
        df = pd.DataFrame([_make_risk_row(overall_risk_score=92.0, risk_level="CRITICAL")])
        alerts = prioritizer.prioritize(df, single_explanation, single_recommendation)
        assert alerts[0].priority == AlertPriority.P1_CRITICAL

    def test_high_score_maps_to_p2(self, prioritizer, single_recommendation):
        df = pd.DataFrame([_make_risk_row(overall_risk_score=77.0, risk_level="HIGH")])
        exp = [_make_explanation("TXN001", 77.0)]
        alerts = prioritizer.prioritize(df, exp, single_recommendation)
        assert alerts[0].priority == AlertPriority.P2_HIGH

    def test_medium_score_maps_to_p3(self, prioritizer, single_recommendation):
        df = pd.DataFrame([_make_risk_row(overall_risk_score=55.0, risk_level="MEDIUM")])
        exp = [_make_explanation("TXN001", 55.0)]
        alerts = prioritizer.prioritize(df, exp, single_recommendation)
        assert alerts[0].priority == AlertPriority.P3_MEDIUM

    def test_low_score_maps_to_p4(self, prioritizer):
        df = pd.DataFrame([_make_risk_row(overall_risk_score=10.0, risk_level="LOW",
                                          triggered_rules=[], triggered_patterns=[])])
        alerts = prioritizer.prioritize(df, [], {})
        assert alerts[0].priority == AlertPriority.P4_LOW

    def test_explanation_narrative_used(self, prioritizer, single_row_df, single_explanation, single_recommendation):
        alert = prioritizer.prioritize(single_row_df, single_explanation, single_recommendation)[0]
        assert "CRITICAL" in alert.narrative

    def test_recommendations_attached(self, prioritizer, single_row_df, single_explanation, single_recommendation):
        alert = prioritizer.prioritize(single_row_df, single_explanation, single_recommendation)[0]
        assert len(alert.recommendations) == 1
        assert alert.recommendations[0].action == RecommendedAction.FILE_SAR


# ---------------------------------------------------------------------------
# Tests — sorting
# ---------------------------------------------------------------------------

class TestSorting:

    def test_higher_priority_alert_comes_first(self, prioritizer, single_recommendation):
        rows = [
            _make_risk_row(transaction_id="TXN002", overall_risk_score=55.0, risk_level="MEDIUM"),
            _make_risk_row(transaction_id="TXN001", overall_risk_score=90.0, risk_level="CRITICAL"),
        ]
        df = pd.DataFrame(rows)
        exps = [_make_explanation("TXN001", 90.0), _make_explanation("TXN002", 55.0)]
        recs = {
            "TXN001": [_make_recommendation("TXN001")],
            "TXN002": [_make_recommendation("TXN002")],
        }
        alerts = prioritizer.prioritize(df, exps, recs)

        assert alerts[0].priority == AlertPriority.P1_CRITICAL
        assert alerts[1].priority == AlertPriority.P3_MEDIUM

    def test_tie_broken_by_risk_score(self, prioritizer):
        rows = [
            _make_risk_row(transaction_id="TXN_A", overall_risk_score=76.0, risk_level="HIGH"),
            _make_risk_row(transaction_id="TXN_B", overall_risk_score=80.0, risk_level="HIGH"),
        ]
        df = pd.DataFrame(rows)
        alerts = prioritizer.prioritize(df, [], {})

        assert alerts[0].transaction_id == "TXN_B"
        assert alerts[1].transaction_id == "TXN_A"


# ---------------------------------------------------------------------------
# Tests — deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:

    def test_duplicate_txn_ids_deduplicated(self, prioritizer):
        rows = [
            _make_risk_row(transaction_id="TXN001"),
            _make_risk_row(transaction_id="TXN001"),  # duplicate
        ]
        df = pd.DataFrame(rows)
        alerts = prioritizer.prioritize(df, [], {})
        assert len(alerts) == 1
