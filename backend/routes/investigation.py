from fastapi import APIRouter

router = APIRouter(prefix="/investigation", tags=["Investigation"])

@router.get("/{transaction_id}")
def get_investigation_details(transaction_id: str):
    return {"transaction_id": transaction_id, "details": {}}
