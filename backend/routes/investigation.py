import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from backend.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Investigation"])
ai_service = AIService()

class InvestigationNote(BaseModel):
    note: str
    status: str

@router.get("/investigation/{alert_id}")
def get_investigation_details(alert_id: str) -> Dict[str, Any]:
    """
    Return investigation details fetched from the AI service.
    """
    try:
        data = ai_service.get_investigation(alert_id)
        if not data:
            raise HTTPException(status_code=404, detail="Investigation not found.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch investigation {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving investigation details.")

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
