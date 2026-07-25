"""
Alerts Package
==============
Converts engine outputs into ranked, deduplicated, structured Alert objects.

The AlertPrioritizer:
  - Assigns P1/P2/P3/P4 priority based on fused risk score
  - Deduplicates alerts for the same account within the suppression window
  - Caps total alert count per run (configurable via engine_config.yaml)
  - Returns a time-sorted list of Alert dataclass instances

The Alert dataclass is the final output consumed by the API Interface
(and ultimately the FastAPI backend built by another developer).

Usage:
    from src.alerts.alert_prioritizer import AlertPrioritizer, Alert

    prioritizer = AlertPrioritizer()
    alerts = prioritizer.prioritize(risk_df, explanations, recommendations)
"""
from src.alerts.alert_prioritizer import AlertPrioritizer, Alert

__all__ = ["AlertPrioritizer", "Alert"]
