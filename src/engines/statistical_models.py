from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class StatisticalSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class StatisticalFinding:
    """
    Represents a detected mathematical or statistical anomaly for a transaction.
    """
    finding_id: str
    finding_name: str
    severity: StatisticalSeverity
    score: float
    triggered: bool
    customer_id: str
    transaction_id: str
    metric_name: str
    metric_value: float
    expected_value: float
    deviation: float
    confidence: float
    explanation: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
