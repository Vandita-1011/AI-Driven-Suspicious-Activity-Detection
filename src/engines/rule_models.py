from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from datetime import datetime

class RuleSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class RuleHit:
    """
    Represents a triggered AML rule against a single transaction.
    """
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    score: float
    triggered: bool
    reason: str
    explanation: str
    evidence: dict[str, Any]
    customer_id: str
    transaction_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
