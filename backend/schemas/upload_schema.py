# pyrefly: ignore [missing-import]
from typing import Optional
from pydantic import BaseModel

class UploadResponse(BaseModel):
    status: str
    message: str
    file_name: str
    request_id: Optional[str] = None
    investigation_id: Optional[str] = None

class AnalysisResponse(BaseModel):
    status: str
    message: str
