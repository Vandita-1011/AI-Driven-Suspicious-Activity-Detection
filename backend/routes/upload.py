# pyrefly: ignore [missing-import]
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.ai_service import AIService
from backend.schemas.upload_schema import UploadResponse, AnalysisResponse

router = APIRouter(tags=["Analysis & Upload"])
ai_service = AIService()

@router.post("/upload-transactions", response_model=UploadResponse)
async def upload_transactions(file: UploadFile = File(...)):
    """
    Accept CSV upload and process it via AI service.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    result = ai_service.process_uploaded_file(file)
    return UploadResponse(
        status=result["status"],
        message="Data uploaded successfully",
        file_name=result["file_name"]
    )

@router.post("/run-analysis", response_model=AnalysisResponse)
def run_analysis():
    """
    Trigger the AI analysis pipeline.
    """
    result = ai_service.run_analysis()
    return AnalysisResponse(
        status=result["status"],
        message=result["message"]
    )
