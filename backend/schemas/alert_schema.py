from pydantic import BaseModel

class AlertResponse(BaseModel):
    alert_id: str
    severity: str
    description: str
