import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.ai_service import AIService
from backend.models.ai_request import InvestigationRequest
from backend.exceptions.ai_exceptions import (
    AIValidationError,
    AITimeoutError,
    AIConnectionError,
    AIUnavailableError,
)
from backend.schemas.upload_schema import UploadResponse, AnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis & Upload"])
ai_service = AIService()

@router.post("/upload-transactions", response_model=UploadResponse)
async def upload_transactions(file: UploadFile = File(...)):
    """
    Accept CSV upload, validate file, generate investigation ID & request ID,
    and submit to AI Integration Layer.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        logger.warning(f"Invalid file extension uploaded: {file.filename}")
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    try:
        # Validate upload file
        ai_service.upload_transactions(file)

        # Create metadata IDs
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        investigation_id = f"inv_{uuid.uuid4().hex[:8]}"

        # Submit investigation to AI Integration Layer
        inv_request = InvestigationRequest(
            request_id=request_id,
            investigation_id=investigation_id,
            parameters={"file_name": file.filename}
        )
        inv_response = ai_service.submit_investigation(inv_request)

        return UploadResponse(
            status=inv_response.status,
            message="Data uploaded and investigation initiated successfully.",
            file_name=file.filename,
            request_id=inv_response.request_id,
            investigation_id=inv_response.investigation_id
        )
    except AIValidationError as e:
        logger.error(f"Validation error during upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AITimeoutError as e:
        logger.error(f"AI Service timeout during upload: {e}")
        raise HTTPException(status_code=504, detail="AI Service request timed out.")
    except (AIConnectionError, AIUnavailableError) as e:
        logger.error(f"AI Service unavailable during upload: {e}")
        raise HTTPException(status_code=503, detail="AI Service is currently unavailable.")
    except Exception as e:
        logger.error(f"Failed to upload transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload.")

@router.post("/run-analysis", response_model=AnalysisResponse)
def run_analysis():
    """
    Trigger the AI analysis pipeline.
    """
    try:
        result = ai_service.run_analysis()
        return AnalysisResponse(
            status=result["status"],
            message=result["message"]
        )
    except Exception as e:
        logger.error(f"Failed to run analysis: {e}")
        raise HTTPException(status_code=500, detail="Error running analysis.")
