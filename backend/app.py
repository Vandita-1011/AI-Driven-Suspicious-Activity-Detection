from fastapi import FastAPI
from .routes import upload, alerts, dashboard, investigation, reports

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

@app.get("/")
def root():
    return {"message": "AML Backend Running"}
