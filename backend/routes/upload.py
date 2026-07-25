from fastapi import APIRouter

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/")
def upload_data():
    return {"status": "success", "message": "Data uploaded successfully"}
