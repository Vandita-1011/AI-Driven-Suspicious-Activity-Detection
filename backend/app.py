import logging
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
from backend.routes import upload, alerts, dashboard, investigation, reports, feedback
from backend.services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AML Backend",
    description="Backend API for AI-Driven Suspicious Activity Detection",
    version="1.0.0"
)

app.include_router(upload.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(investigation.router)
app.include_router(reports.router)
app.include_router(feedback.router)

ai_service = AIService()

@app.get("/")
def root() -> dict:
    """
    Health check endpoint.
    """
    try:
        health_status = ai_service.health_check()
        return {"message": "AML Backend Running", "ai_status": health_status}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
