"""
Base Explainer Interface
========================
Defines the contract for explanation generation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List

from src.fusion.risk_models import RiskAssessment
from src.engines.rule_models import RuleHit
from src.engines.behaviour_models import BehaviourFinding
from src.engines.statistical_models import StatisticalFinding
from src.engines.ml_models import MLFinding
from src.engines.pattern_models import PatternFinding


@dataclass
class Explanation:
    """
    Evidence-based explanation for a transaction's risk score.
    """
    transaction_id: str
    risk_score: float
    narrative: str
    contributing_factors: list[dict[str, Any]] = field(default_factory=list)
    triggered_rules: list[str] = field(default_factory=list)
    matched_patterns: list[str] = field(default_factory=list)


class BaseExplainer(ABC):
    """
    Abstract base class for explainers.
    """

    @abstractmethod
    def explain(
        self,
        risk_assessment: RiskAssessment,
        rule_hits: List[RuleHit],
        behaviour_findings: List[BehaviourFinding],
        stat_findings: List[StatisticalFinding],
        ml_findings: List[MLFinding],
        pattern_findings: List[PatternFinding]
    ) -> Explanation:
        """
        Generates an explanation for a single transaction based on actual findings.
        """
        pass

    @abstractmethod
    def explain_batch(
        self,
        risk_assessments: List[RiskAssessment],
        rule_hits: List[RuleHit],
        behaviour_findings: List[BehaviourFinding],
        stat_findings: List[StatisticalFinding],
        ml_findings: List[MLFinding],
        pattern_findings: List[PatternFinding]
    ) -> List[Explanation]:
        """
        Generates explanations for a batch of transactions.
        """
        pass
