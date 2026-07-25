from pydantic import BaseModel

class UploadResponse(BaseModel):
    status: str
    message: str
    file_name: str

class AnalysisResponse(BaseModel):
    status: str
    message: str
