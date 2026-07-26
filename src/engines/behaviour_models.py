from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class BehaviourSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class BehaviourFinding:
    """
    Represents a detected anomaly comparing a transaction to historical customer behaviour.
    """
    finding_id: str
    finding_name: str
    severity: BehaviourSeverity
    score: float
    triggered: bool
    customer_id: str
    transaction_id: str
    behaviour_type: str
    expected_behaviour: str
    observed_behaviour: str
    deviation: float
    confidence: float
    explanation: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
