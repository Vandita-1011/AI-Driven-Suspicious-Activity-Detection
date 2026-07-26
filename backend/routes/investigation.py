import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.services.ai_service import AIService
from backend.exceptions.ai_exceptions import (
    AIValidationError,
    AITimeoutError,
    AIConnectionError,
    AIUnavailableError,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Investigation"])
ai_service = AIService()

class InvestigationNote(BaseModel):
    note: str
    status: str

@router.get("/investigation/{alert_id}/status")
def get_investigation_status(alert_id: str) -> Dict[str, Any]:
    """
    Track status and progress of an ongoing investigation.
    """
    try:
        status_resp = ai_service.get_investigation_status(investigation_id=alert_id)
        return {
            "request_id": status_resp.request_id,
            "investigation_id": status_resp.investigation_id,
            "status": status_resp.status,
            "progress": status_resp.progress_percentage or 100.0,
            "message": f"Investigation status is {status_resp.status}"
        }
    except AIValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AITimeoutError as e:
        raise HTTPException(status_code=504, detail="AI Service status query timed out.")
    except (AIConnectionError, AIUnavailableError) as e:
        raise HTTPException(status_code=503, detail="AI Service is currently unavailable.")
    except Exception as e:
        logger.error(f"Failed to fetch status for {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching investigation status.")

@router.get("/investigation/{alert_id}/result")
@router.get("/investigation/{alert_id}")
def get_investigation_details(alert_id: str) -> Dict[str, Any]:
    """
    Return investigation result object from AI Integration Layer.
    """
    try:
        data = ai_service.get_investigation(alert_id)
        if not data:
            raise HTTPException(status_code=404, detail="Investigation not found.")
        return data
    except AIValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch investigation {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving investigation details.")

@router.post("/investigation/{alert_id}/cancel")
def cancel_investigation(alert_id: str) -> Dict[str, Any]:
    """
    Cancel an active investigation.
    """
    try:
        cancel_resp = ai_service.cancel_investigation(investigation_id=alert_id)
        return {
            "request_id": cancel_resp.request_id,
            "investigation_id": cancel_resp.investigation_id,
            "status": cancel_resp.status,
            "message": cancel_resp.message or "Investigation cancelled."
        }
    except Exception as e:
        logger.error(f"Failed to cancel investigation {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error cancelling investigation.")

@router.post("/investigation/{alert_id}")
def update_investigation(alert_id: str, payload: InvestigationNote) -> Dict[str, Any]:
    """
    Accept investigation notes/status update and pass to AI service.
    """
    try:
        return ai_service.update_investigation(alert_id, payload)
    except Exception as e:
        logger.error(f"Failed to update investigation {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating investigation.")
