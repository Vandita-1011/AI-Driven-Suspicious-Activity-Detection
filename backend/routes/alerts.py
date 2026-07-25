from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/")
def get_alerts():
    return {"alerts": []}

@router.get("/{alert_id}")
def get_alert(alert_id: str):
    return {"alert_id": alert_id, "status": "details"}
