import logging
from typing import Dict
from fastapi import APIRouter, HTTPException
from backend.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Dashboard"])
ai_service = AIService()

@router.get("/dashboard")
def get_dashboard_summary() -> Dict[str, int]:
    """
    Return dashboard statistics fetched from the AI service.
    """
    try:
        return ai_service.get_dashboard_data()
    except Exception as e:
        logger.error(f"Failed to fetch dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard data.")
