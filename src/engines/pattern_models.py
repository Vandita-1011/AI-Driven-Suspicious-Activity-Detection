from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any
from datetime import datetime


class PatternSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class PatternFinding:
    """
    Represents a detected known AML typology or money laundering pattern.
    """
    pattern_id: str
    pattern_name: str
    severity: PatternSeverity
    confidence: float
    description: str
    evidence: Dict[str, Any]
    customer_id: str
    transaction_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
