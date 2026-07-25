import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from backend.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Reports"])
ai_service = AIService()

@router.get("/reports")
def get_reports() -> Dict[str, List[Dict[str, str]]]:
    """
    Return available reports list fetched from the AI service.
    """
    try:
        reports_data = ai_service.get_reports()
        return {"reports": reports_data}
    except Exception as e:
        logger.error(f"Failed to fetch reports: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving reports.")
