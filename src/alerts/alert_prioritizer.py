"""
Alert Prioritizer
=================
Converts engine outputs into ranked, deduplicated Alert objects.

The AlertPrioritizer:
  - Builds Alert objects from risk_df, explanations, and recommendations.
  - Assigns AlertPriority (P1–P4) from risk score using configurable thresholds.
  - Sorts alerts: highest priority first; ties broken by risk_score → confidence → transaction_id.
  - Caps total alert count per run (configurable via engine_config.yaml).
  - Deduplicates by transaction_id to avoid duplicate entries in one run.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List

import pandas as pd

from src.constants.risk_levels import AlertPriority, RiskLevel
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.timer import timed

logger = get_logger(__name__)

# Default alert status
_STATUS_OPEN = "OPEN"

# AlertPriority numeric order — lower is more urgent
_PRIORITY_ORDER = {
    AlertPriority.P1_CRITICAL: 1,
    AlertPriority.P2_HIGH: 2,
    AlertPriority.P3_MEDIUM: 3,
    AlertPriority.P4_LOW: 4,
}


@dataclass
class Alert:
    """Represents a finalized, actionable alert for the investigator."""

    alert_id: str
    transaction_id: str
    customer_id: str
    priority: AlertPriority
    fused_risk_score: float
    recommended_action: str
    narrative: str
    timestamp: str

    # Extended fields (new — not breaking existing usage)
    risk_level: str = ""
    confidence_score: float = 0.0
    alert_title: str = ""
    alert_summary: str = ""
    triggered_rules: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    contributing_factors: List[Any] = field(default_factory=list)
    recommendations: List[Any] = field(default_factory=list)
    investigator_action: str = ""
    status: str = _STATUS_OPEN


class AlertPrioritizer:
    """
    Ranks alerts based on severity and deduplicates within a single run.
    """

    def __init__(self) -> None:
        self.settings = get_settings().alerts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_to_priority(self, risk_score: float) -> AlertPriority:
        """Maps a numeric risk score to an AlertPriority using configured thresholds."""
        t = self.settings.priority_thresholds
        if risk_score >= t.get("critical", 90):
            return AlertPriority.P1_CRITICAL
        elif risk_score >= t.get("high", 75):
            return AlertPriority.P2_HIGH
        elif risk_score >= t.get("medium", 50):
            return AlertPriority.P3_MEDIUM
        else:
            return AlertPriority.P4_LOW

    @staticmethod
    def _alert_sort_key(alert: Alert) -> tuple:
        """Sort key: priority order asc, then risk score desc, confidence desc, txn_id asc."""
        return (
            _PRIORITY_ORDER.get(alert.priority, 99),
            -alert.fused_risk_score,
            -alert.confidence_score,
            alert.transaction_id,
        )

    @staticmethod
    def _build_title(risk_level: str, num_rules: int, num_patterns: int) -> str:
        """Generates a concise alert title from key evidence indicators."""
        parts = [f"{risk_level.upper()} Risk"]
        if num_rules:
            parts.append(f"{num_rules} Rule{'s' if num_rules > 1 else ''} Triggered")
        if num_patterns:
            parts.append(f"{num_patterns} Pattern{'s' if num_patterns > 1 else ''} Matched")
        return " | ".join(parts)

    @staticmethod
    def _build_summary(
        transaction_id: str,
        risk_score: float,
        risk_level: str,
        top_reasons: List[str],
        num_rules: int,
        num_patterns: int,
    ) -> str:
        """Produces a one-line human-readable alert summary."""
        summary = (
            f"Transaction {transaction_id} flagged as {risk_level.upper()} "
            f"(score {risk_score:.1f})."
        )
        if top_reasons:
            summary += f" Primary reasons: {'; '.join(top_reasons[:3])}."
        if num_rules:
            summary += f" {num_rules} AML rule(s) triggered."
        if num_patterns:
            summary += f" {num_patterns} laundering pattern(s) matched."
        return summary

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @timed("Alert Prioritization")
    def prioritize(
        self,
        risk_df: pd.DataFrame,
        explanations: list[Any],
        recommendations: dict[str, Any],
    ) -> list[Alert]:
        """
        Creates and sorts Alert objects from pipeline outputs.

        Args:
            risk_df:         DataFrame of RiskAssessment rows.
            explanations:    List of Explanation objects (one per transaction).
            recommendations: Dict[transaction_id → List[Recommendation]].

        Returns:
            Sorted, deduplicated list of Alert objects (highest priority first).
            Capped at settings.alerts.max_alerts.
        """
        logger.info("Prioritizing alerts...")

        if not isinstance(risk_df, pd.DataFrame) or risk_df.empty:
            logger.warning("prioritize() received empty risk_df; returning empty list.")
            return []

        logger.info("Found %d potential alerts before filtering.", len(risk_df))

        # Index explanations by transaction_id for O(1) lookup
        explanation_map: dict[str, Any] = {}
        if explanations:
            for exp in explanations:
                explanation_map[exp.transaction_id] = exp

        now_ts = datetime.now(timezone.utc).isoformat()
        alerts: list[Alert] = []
        seen_txn_ids: set[str] = set()

        for _, row in risk_df.iterrows():
            try:
                tid = str(row.get("transaction_id", ""))
                if not tid or tid in seen_txn_ids:
                    continue
                seen_txn_ids.add(tid)

                risk_score = float(row.get("overall_risk_score", 0.0))
                customer_id = str(row.get("customer_id", ""))
                confidence = float(row.get("confidence_score", 0.0))
                risk_level = str(row.get("risk_level", "LOW"))
                triggered_rules: List[str] = row.get("triggered_rules", []) or []
                triggered_patterns: List[str] = row.get("triggered_patterns", []) or []
                top_reasons: List[str] = row.get("top_reasons", []) or []

                # Resolve AlertPriority from risk score
                priority = self._score_to_priority(risk_score)

                # Explanation data
                exp = explanation_map.get(tid)
                narrative = exp.narrative if exp else ""
                contributing_factors = exp.contributing_factors if exp else []
                exp_rules = exp.triggered_rules if exp else triggered_rules
                exp_patterns = exp.matched_patterns if exp else triggered_patterns

                # Recommendation data — take highest-priority rec for primary fields
                txn_recs = recommendations.get(tid, [])
                primary_action = ""
                if txn_recs:
                    top_rec = txn_recs[0]  # already sorted by priority in Recommender
                    primary_action = (
                        top_rec.suggested_investigator_action
                        if hasattr(top_rec, "suggested_investigator_action")
                        else str(top_rec)
                    )
                    recommended_action_str = (
                        top_rec.action.value
                        if hasattr(top_rec, "action") and hasattr(top_rec.action, "value")
                        else str(getattr(top_rec, "action", ""))
                    )
                else:
                    recommended_action_str = ""

                title = self._build_title(risk_level, len(exp_rules), len(exp_patterns))
                summary = self._build_summary(
                    tid, risk_score, risk_level, top_reasons,
                    len(exp_rules), len(exp_patterns),
                )

                alert = Alert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:12].upper()}",
                    transaction_id=tid,
                    customer_id=customer_id,
                    priority=priority,
                    fused_risk_score=risk_score,
                    recommended_action=recommended_action_str,
                    narrative=narrative,
                    timestamp=now_ts,
                    # Extended fields
                    risk_level=risk_level,
                    confidence_score=confidence,
                    alert_title=title,
                    alert_summary=summary,
                    triggered_rules=exp_rules,
                    matched_patterns=exp_patterns,
                    contributing_factors=contributing_factors,
                    recommendations=txn_recs,
                    investigator_action=primary_action,
                    status=_STATUS_OPEN,
                )
                alerts.append(alert)

            except Exception as exc:
                logger.warning("Skipping alert for row due to error: %s", exc)
                continue

        # Sort: highest priority first, then by risk score desc, confidence desc, txn_id asc
        alerts.sort(key=self._alert_sort_key)

        # Cap at max_alerts
        max_alerts = getattr(self.settings, "max_alerts", 1000)
        if len(alerts) > max_alerts:
            logger.warning(
                "Alert count %d exceeds max_alerts=%d; truncating.",
                len(alerts), max_alerts,
            )
            alerts = alerts[:max_alerts]

        logger.info("Produced %d prioritized alerts.", len(alerts))
        return alerts
