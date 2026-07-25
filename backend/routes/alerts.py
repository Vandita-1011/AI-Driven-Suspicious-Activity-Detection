import logging
from fastapi import APIRouter, HTTPException
from backend.schemas.alert_schema import AlertListResponse, AlertDetailResponse
from backend.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Alerts"])
ai_service = AIService()

@router.get("/alerts", response_model=AlertListResponse)
def get_alerts() -> AlertListResponse:
    """
    Return a list of alerts fetched from the AI service.
    """
    try:
        alerts_data = ai_service.get_alerts()
        return AlertListResponse(alerts=alerts_data)
    except Exception as e:
        logger.error(f"Failed to fetch alerts: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving alerts.")

@router.get("/alerts/{alert_id}", response_model=AlertDetailResponse)
def get_alert(alert_id: str) -> AlertDetailResponse:
    """
    Return details of a specific alert fetched from the AI service.
    """
    try:
        alert_data = ai_service.get_alert(alert_id)
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alert not found.")
        return AlertDetailResponse(**alert_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving alert details.")
