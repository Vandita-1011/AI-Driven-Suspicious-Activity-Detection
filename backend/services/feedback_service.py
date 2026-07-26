import uuid
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self):
        # Mock storage for analyst feedback
        self.feedbacks = {}

    def add_feedback(self, investigation_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store analyst feedback for an investigation."""
        feedback_id = f"FB-{uuid.uuid4().hex[:6].upper()}"
        
        feedback_record = {
            "feedback_id": feedback_id,
            "investigation_id": investigation_id,
            "rating": feedback_data.get("rating"),
            "notes": feedback_data.get("notes"),
            "analyst_id": feedback_data.get("analyst_id", "Current_User"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "decision_override": feedback_data.get("decision_override")
        }
        
        if investigation_id not in self.feedbacks:
            self.feedbacks[investigation_id] = []
            
        self.feedbacks[investigation_id].append(feedback_record)
        return feedback_record

    def get_feedback(self, investigation_id: str) -> List[Dict[str, Any]]:
        """Retrieve feedback history for an investigation."""
        return self.feedbacks.get(investigation_id, [])
