"""
Engines Package
===============
Five detection engines plus the Smart Risk Fusion layer.

Each engine implements BaseDetectionEngine and returns an EngineResult.
The Orchestrator runs them in sequence and passes results to RiskFusion.

Engines (run in this order):
    RuleEngine          Hard rule-based flags (thresholds, FATF, PEP, dormant)
    BehaviourEngine     Deviation from customer behaviour baseline
    StatisticalEngine   Z-score and IQR anomaly detection
    MLEngine            Isolation Forest unsupervised anomaly scoring
    AMLPatternEngine    Pattern matching for all 15 AML scenarios
    SmartRiskFusion     Weighted combination → unified risk score [0–100]

Usage:
    from src.engines.rule_engine import RuleEngine
    from src.engines.risk_fusion import SmartRiskFusion
"""
from src.engines.rule_engine import RuleEngine
from src.engines.behaviour_engine import BehaviourEngine
from src.engines.statistical_engine import StatisticalEngine
from src.engines.ml_engine import MLEngine
from src.engines.aml_pattern_engine import AMLPatternEngine
from src.engines.risk_fusion import SmartRiskFusion

__all__ = [
    "RuleEngine", "BehaviourEngine", "StatisticalEngine",
    "MLEngine", "AMLPatternEngine", "SmartRiskFusion",
]
