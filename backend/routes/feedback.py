import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from backend.services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Feedback"])
feedback_service = FeedbackService()

class FeedbackRequest(BaseModel):
    investigation_id: str
    rating: int
    notes: str
    decision_override: str = None
    analyst_id: str = "Current_User"

@router.post("/feedback")
def submit_feedback(request: FeedbackRequest) -> Dict[str, Any]:
    """
    Submit feedback for an investigation.
    """
    try:
        record = feedback_service.add_feedback(
            investigation_id=request.investigation_id,
            feedback_data=request.model_dump()
        )
        return {"status": "success", "message": "Feedback saved successfully", "data": record}
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail="Error saving feedback.")

@router.get("/feedback/{investigation_id}")
def get_feedback(investigation_id: str) -> Dict[str, Any]:
    """
    Get all feedback for an investigation.
    """
    try:
        records = feedback_service.get_feedback(investigation_id)
        return {"feedback": records}
    except Exception as e:
        logger.error(f"Failed to fetch feedback for {investigation_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving feedback.")
