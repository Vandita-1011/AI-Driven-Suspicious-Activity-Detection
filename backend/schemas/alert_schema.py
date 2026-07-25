from pydantic import BaseModel
from typing import List, Dict, Any

class AlertBase(BaseModel):
    alert_id: str
    severity: str
    description: str

class AlertListResponse(BaseModel):
    alerts: List[AlertBase]

class AlertDetailResponse(BaseModel):
    alert_id: str
    severity: str
    description: str
    details: Dict[str, Any]
