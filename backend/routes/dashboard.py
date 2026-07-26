import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from backend.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Dashboard"])
dashboard_service = DashboardService()


@router.get("/dashboard")
def get_dashboard() -> Dict[str, Any]:
    """
    Return full dashboard payload including summary, risk distribution,
    trend data, and recent activity.
    """
    try:
        return dashboard_service.get_full_dashboard()
    except Exception as e:
        logger.error(f"Failed to fetch dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard data.")


@router.get("/dashboard/summary")
def get_dashboard_summary() -> Dict[str, Any]:
    """
    Return only the KPI summary metrics.
    """
    try:
        return dashboard_service.get_summary()
    except Exception as e:
        logger.error(f"Failed to fetch dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard summary.")


@router.get("/dashboard/trend")
def get_dashboard_trend() -> List[Dict[str, Any]]:
    """
    Return transaction volume trend data.
    """
    try:
        return dashboard_service.get_trend()
    except Exception as e:
        logger.error(f"Failed to fetch dashboard trend: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard trend.")


@router.get("/dashboard/risk-distribution")
def get_risk_distribution() -> List[Dict[str, Any]]:
    """
    Return risk distribution data.
    """
    try:
        return dashboard_service.get_risk_distribution()
    except Exception as e:
        logger.error(f"Failed to fetch risk distribution: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving risk distribution.")
