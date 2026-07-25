from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MLFinding:
    """
    Represents an unsupervised machine learning anomaly prediction for a transaction.
    """
    finding_id: str
    model_name: str
    prediction: str  # 'Normal' or 'Anomaly'
    anomaly_score: float
    confidence: float
    customer_id: str
    transaction_id: str
    explanation: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
