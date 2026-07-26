from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any
from datetime import datetime


class RiskLevel(str, Enum):
    LOW = "LOW"             # 0-20
    MEDIUM = "MEDIUM"       # 21-40
    HIGH = "HIGH"           # 41-60
    VERY_HIGH = "VERY HIGH" # 61-80
    CRITICAL = "CRITICAL"   # 81-100


@dataclass
class EngineContribution:
    engine_name: str
    score: float
    weight: float
    weighted_score: float
    raw_findings_count: int


@dataclass
class RiskAssessment:
    """
    Unified risk assessment representing the fused output of all detection engines.
    """
    transaction_id: str
    customer_id: str
    overall_risk_score: float
    confidence_score: float
    risk_level: RiskLevel
    engine_scores: Dict[str, float]
    engine_weights: Dict[str, float]
    supporting_evidence: Dict[str, List[Any]]
    triggered_rules: List[str]
    triggered_patterns: List[str]
    top_reasons: List[str]
    risk_breakdown: Dict[str, str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
