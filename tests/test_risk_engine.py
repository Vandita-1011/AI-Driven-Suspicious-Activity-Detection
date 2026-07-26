# pyrefly: ignore [missing-import]
import pytest

from src.engines.rule_models import RuleHit, RuleSeverity
from src.engines.behaviour_models import BehaviourFinding, BehaviourSeverity
from src.engines.statistical_models import StatisticalFinding, StatisticalSeverity
from src.engines.ml_models import MLFinding
from src.engines.pattern_models import PatternFinding, PatternSeverity

from src.fusion.risk_engine import RiskEngine
from src.fusion.risk_models import RiskLevel


@pytest.fixture
def sample_rule_hits():
    return [
        RuleHit(
            rule_id="R001", rule_name="Large Transaction", severity=RuleSeverity.HIGH, score=80.0,
            triggered=True, reason="amount", explanation="large", evidence={}, 
            customer_id="CUST1", transaction_id="TXN1", timestamp="2024-01-01T10:00:00"
        ),
        RuleHit(
            rule_id="R013", rule_name="High Risk Country", severity=RuleSeverity.CRITICAL, score=95.0,
            triggered=True, reason="country", explanation="high risk", evidence={}, 
            customer_id="CUST1", transaction_id="TXN1", timestamp="2024-01-01T10:00:00"
        )
    ]

@pytest.fixture
def sample_behaviour_findings():
    return [
        BehaviourFinding(
            finding_id="B009", finding_name="Country Behaviour Change", severity=BehaviourSeverity.HIGH, score=80.0,
            triggered=True, customer_id="CUST1", transaction_id="TXN1", behaviour_type="geographic",
            expected_behaviour="domestic", observed_behaviour="foreign", deviation=1.0, confidence=0.9,
            explanation="new country", timestamp="2024-01-01T10:00:00"
        )
    ]

@pytest.fixture
def sample_stat_findings():
    return [
        StatisticalFinding(
            finding_id="S001", finding_name="Amount Z-Score", severity=StatisticalSeverity.HIGH, score=75.0,
            triggered=True, customer_id="CUST1", transaction_id="TXN1", metric_name="z_score",
            metric_value=4.0, expected_value=0.0, deviation=4.0, confidence=0.85,
            explanation="z score 4.0", timestamp="2024-01-01T10:00:00"
        )
    ]

@pytest.fixture
def sample_ml_findings():
    return [
        MLFinding(
            finding_id="ML001", model_name="IsolationForest_v1", prediction="Anomaly",
            anomaly_score=0.25, confidence=0.90, customer_id="CUST1", transaction_id="TXN1",
            explanation="Anomaly detected.", timestamp="2024-01-01T10:00:00"
        )
    ]

@pytest.fixture
def sample_pattern_findings():
    return [
        PatternFinding(
            pattern_id="P008", pattern_name="Cross-Border Layering", severity=PatternSeverity.CRITICAL,
            confidence=0.95, description="cross border movement", evidence={},
            customer_id="CUST1", transaction_id="TXN1", timestamp="2024-01-01T10:00:00"
        )
    ]


def test_empty_inputs():
    engine = RiskEngine()
    assessments = engine.run([], [], [], [], [])
    assert len(assessments) == 0


def test_partial_inputs_adaptive_weighting(sample_rule_hits):
    engine = RiskEngine()
    # Provide ONLY rule hits. 
    # Adaptive weighting should reallocate 100% of the weight to Rule Engine.
    assessments = engine.run(sample_rule_hits, [], [], [], [])
    
    assert len(assessments) == 1
    assessment = assessments[0]
    
    # Weights should be 1.0 for Rule and 0.0 for others
    assert assessment.engine_weights["Rule"] == 1.0
    assert assessment.engine_weights["Pattern"] == 0.0
    
    # Total score should be equal to the rule score, which is min(100, 80+95) = 100.
    assert assessment.overall_risk_score == 100.0
    assert assessment.risk_level == RiskLevel.CRITICAL


def test_full_fusion(
    sample_rule_hits, sample_behaviour_findings, sample_stat_findings, 
    sample_ml_findings, sample_pattern_findings
):
    engine = RiskEngine()
    assessments = engine.run(
        sample_rule_hits, sample_behaviour_findings, sample_stat_findings, 
        sample_ml_findings, sample_pattern_findings
    )
    
    assert len(assessments) == 1
    assessment = assessments[0]
    
    assert assessment.transaction_id == "TXN1"
    assert assessment.customer_id == "CUST1"
    
    # Rule score: min(100, 80+95) = 100
    # Behaviour score: 80
    # Stat score: 75
    # ML score: 0.90 * 100 = 90
    # Pattern score: CRITICAL -> 100
    
    # Check breakdown format
    assert "30.0%" in assessment.risk_breakdown["Rule"]
    
    # Check top reasons
    assert "High Risk Country" in assessment.top_reasons
    assert "Cross-Border Layering" in assessment.top_reasons
    
    assert assessment.overall_risk_score > 80.0
    assert assessment.risk_level == RiskLevel.CRITICAL
    assert assessment.confidence_score > 80.0
