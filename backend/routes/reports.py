from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/")
def get_reports():
    return {"reports": []}

@router.post("/generate")
def generate_report():
    return {"status": "success", "message": "Report generation started"}
