import uuid
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self):
        # Mock storage for generated reports
        self.reports = []

    def generate_report(self, report_type: str, format: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a new report and store it in the mock history."""
        metadata = metadata or {}
        report_id = f"REP-{uuid.uuid4().hex[:6].upper()}"
        report = {
            "id": report_id,
            "alertId": metadata.get("alert_id", "Multiple"),
            "customer": metadata.get("customer", "System"),
            "type": report_type,
            "status": "Generated",
            "generatedOn": datetime.utcnow().isoformat() + "Z",
            "format": format.upper(),
            "riskLevel": metadata.get("riskLevel", "N/A")
        }
        self.reports.append(report)
        return report

    def get_historical_reports(self) -> List[Dict[str, Any]]:
        """Return all generated reports."""
        return self.reports

    def delete_report(self, report_id: str) -> bool:
        """Delete a report by ID."""
        initial_count = len(self.reports)
        self.reports = [r for r in self.reports if r["id"] != report_id]
        return len(self.reports) < initial_count
