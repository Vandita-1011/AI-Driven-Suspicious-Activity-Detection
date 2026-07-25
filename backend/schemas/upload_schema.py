from pydantic import BaseModel

class UploadRequest(BaseModel):
    file_name: str
    file_size: int
