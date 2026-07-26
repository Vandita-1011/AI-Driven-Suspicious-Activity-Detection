"""
Dashboard Service
=================
Aggregates dashboard metrics from the AI Integration Layer.
All TODO stubs in this file should be replaced with real AI data
once Vandita's Public AI Interface is merged.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List

from backend.services.ai_service import AIService

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Aggregates and structures dashboard data for the frontend.
    Communicates exclusively through the AIService layer.
    """

    def __init__(self, ai_service: AIService = None):
        self.ai_service = ai_service or AIService()

    def get_full_dashboard(self) -> Dict[str, Any]:
        """
        Returns the complete dashboard payload combining summary,
        risk distribution, trend data, and recent activity.
        """
        return {
            "summary": self.get_summary(),
            "risk_distribution": self.get_risk_distribution(),
            "trend": self.get_trend(),
            "recent_activity": self.get_recent_activity(),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Returns aggregated KPI summary metrics.
        """
        raw = self.ai_service.get_dashboard_data()

        # TODO: Replace stub investigation metrics with real data from
        # Vandita's Public AI Interface after branch merge.
        active_investigations = 5
        closed_investigations = 12
        total_investigations = active_investigations + closed_investigations
        success_rate = round(
            (closed_investigations / total_investigations * 100) if total_investigations > 0 else 0.0, 1
        )

        return {
            "total_transactions": raw.get("total_alerts", 0),
            "high_risk": raw.get("high_risk", 0),
            "medium_risk": raw.get("medium_risk", 0),
            "low_risk": raw.get("low_risk", 0),
            "active_investigations": active_investigations,
            "closed_investigations": closed_investigations,
            "total_investigations": total_investigations,
            "success_rate": success_rate,
        }

    def get_risk_distribution(self) -> List[Dict[str, Any]]:
        """
        Returns risk distribution data formatted for the PieChart.
        """
        raw = self.ai_service.get_dashboard_data()

        return [
            {"name": "High", "value": raw.get("high_risk", 0)},
            {"name": "Medium", "value": raw.get("medium_risk", 0)},
            {"name": "Low", "value": raw.get("low_risk", 0)},
        ]

    def get_trend(self) -> List[Dict[str, Any]]:
        """
        Returns transaction volume trend data for the BarChart.
        """
        # TODO: Replace with real trend data from Vandita's Public AI
        # Interface / analytics pipeline after branch merge.
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        volumes = [4200, 3800, 5100, 4700, 6200, 3200, 2800]

        return [
            {"name": days[i], "volume": volumes[i]}
            for i in range(len(days))
        ]

    def get_recent_activity(self) -> List[Dict[str, Any]]:
        """
        Returns recent transaction activity for the dashboard table.
        """
        # TODO: Replace with real recent activity from Vandita's Public AI
        # Interface / alert prioritizer after branch merge.
        return [
            {"id": "TXN-78234", "customer": "Global Trade Ltd", "risk": "HIGH", "status": "Pending Review"},
            {"id": "TXN-78190", "customer": "Oceanic Imports", "risk": "MEDIUM", "status": "In Progress"},
            {"id": "TXN-78145", "customer": "Northern Finance", "risk": "HIGH", "status": "Escalated"},
            {"id": "TXN-78102", "customer": "Apex Holdings", "risk": "LOW", "status": "Cleared"},
            {"id": "TXN-78067", "customer": "Summit Corp", "risk": "MEDIUM", "status": "Pending Review"},
        ]
