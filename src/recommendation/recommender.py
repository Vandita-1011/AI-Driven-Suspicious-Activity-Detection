"""
Recommender
===========
Maps fused risk scores and scenario evidence to concrete investigator actions.

Produces structured Recommendation objects from RiskAssessment outputs.
Each transaction receives one or more prioritised, actionable recommendations
based on risk level, triggered rules, matched AML patterns, and engine findings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

import pandas as pd

from src.constants.risk_levels import RecommendedAction, RiskLevel
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Recommendation priority constants (lower int = more urgent)
# ---------------------------------------------------------------------------
_PRIORITY_CRITICAL = 1
_PRIORITY_HIGH = 2
_PRIORITY_MEDIUM = 3
_PRIORITY_LOW = 4

# Risk-level thresholds matching risk_models.RiskLevel ranges
_THRESHOLD_CRITICAL = 81.0
_THRESHOLD_VERY_HIGH = 61.0
_THRESHOLD_HIGH = 41.0
_THRESHOLD_MEDIUM = 21.0


@dataclass
class Recommendation:
    """Structured investigator recommendation for a single transaction."""

    transaction_id: str
    title: str
    description: str
    priority: int                        # 1 = most urgent
    reason: str
    action: RecommendedAction
    suggested_investigator_action: str
    triggered_by: List[str] = field(default_factory=list)


class Recommender:
    """
    Determines the next best action(s) for an investigator based on
    the fused risk assessment outputs.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(
        self,
        transaction_id: str,
        customer_id: str,
        risk_score: float,
        risk_level: str,
        confidence_score: float,
        triggered_rules: List[str],
        triggered_patterns: List[str],
        supporting_evidence: dict[str, List[Any]],
        top_reasons: List[str],
    ) -> List[Recommendation]:
        """
        Returns a prioritised list of Recommendation objects for a single
        transaction based on risk severity and evidence.

        Args:
            transaction_id:     Unique transaction identifier.
            customer_id:        Associated customer identifier.
            risk_score:         Overall fused risk score (0–100).
            risk_level:         Risk level string from RiskAssessment.
            confidence_score:   Engine confidence (0–1).
            triggered_rules:    List of triggered AML rule names.
            triggered_patterns: List of matched laundering pattern names.
            supporting_evidence: Engine-keyed dict of finding objects.
            top_reasons:        Human-readable top risk reasons.

        Returns:
            List of Recommendation, ordered by priority (ascending).
        """
        recs: List[Recommendation] = []
        level = risk_level.upper() if isinstance(risk_level, str) else str(risk_level)
        behaviour_findings = supporting_evidence.get("Behaviour", [])
        stat_findings = supporting_evidence.get("Statistical", [])
        ml_findings = supporting_evidence.get("ML", [])

        # ----------------------------------------------------------------
        # 1. Primary action — driven by overall risk level
        # ----------------------------------------------------------------
        if level == "CRITICAL" or risk_score >= _THRESHOLD_CRITICAL:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="File Suspicious Activity Report",
                description=(
                    "Transaction has been classified as CRITICAL risk. "
                    "Regulatory obligation requires immediate SAR filing."
                ),
                priority=_PRIORITY_CRITICAL,
                reason=f"Risk score {risk_score:.1f} exceeds CRITICAL threshold. Top reasons: {'; '.join(top_reasons)}",
                action=RecommendedAction.FILE_SAR,
                suggested_investigator_action=(
                    "Complete SAR form with transaction details, triggered rules, "
                    "and matched patterns. Submit to Financial Intelligence Unit within 24 hours."
                ),
                triggered_by=triggered_rules + triggered_patterns,
            ))
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Freeze Transaction Pending Investigation",
                description="Halt transaction processing until investigation is complete.",
                priority=_PRIORITY_CRITICAL,
                reason="CRITICAL risk level warrants immediate account action.",
                action=RecommendedAction.FREEZE_ACCOUNT,
                suggested_investigator_action=(
                    "Place a hold on the account. Notify operations team. "
                    "Document freeze timestamp and authorising officer."
                ),
                triggered_by=triggered_rules,
            ))

        elif level == "VERY HIGH" or risk_score >= _THRESHOLD_VERY_HIGH:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Escalate to Compliance Team",
                description=(
                    "Transaction has been classified VERY HIGH risk. "
                    "Requires senior compliance officer review before release."
                ),
                priority=_PRIORITY_CRITICAL,
                reason=f"Risk score {risk_score:.1f}. Triggered rules: {', '.join(triggered_rules) or 'None'}.",
                action=RecommendedAction.ESCALATE_TO_COMPLIANCE,
                suggested_investigator_action=(
                    "Refer case to Level-2 AML compliance officer. "
                    "Attach full evidence bundle including rule hits and pattern matches."
                ),
                triggered_by=triggered_rules + triggered_patterns,
            ))

        elif level == "HIGH" or risk_score >= _THRESHOLD_HIGH:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Manual Investigator Review Required",
                description="HIGH risk transaction requires manual review before case closure.",
                priority=_PRIORITY_HIGH,
                reason=f"Risk score {risk_score:.1f}. Evidence: {'; '.join(top_reasons)}",
                action=RecommendedAction.ESCALATE_TO_COMPLIANCE,
                suggested_investigator_action=(
                    "Assign to AML investigator queue. Review transaction history "
                    "for the past 90 days. Verify counterparty legitimacy."
                ),
                triggered_by=triggered_rules + triggered_patterns,
            ))

        elif level == "MEDIUM" or risk_score >= _THRESHOLD_MEDIUM:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Enhanced Due Diligence Required",
                description="MEDIUM risk transaction. Collect supporting documentation.",
                priority=_PRIORITY_MEDIUM,
                reason=f"Risk score {risk_score:.1f}. Evidence from {len(triggered_rules)} rules.",
                action=RecommendedAction.REQUEST_DOCUMENTS,
                suggested_investigator_action=(
                    "Contact customer for source of funds documentation. "
                    "Set follow-up reminder for 5 business days."
                ),
                triggered_by=triggered_rules,
            ))

        else:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Continue Monitoring",
                description="LOW risk transaction. No immediate action required.",
                priority=_PRIORITY_LOW,
                reason=f"Risk score {risk_score:.1f} is within acceptable thresholds.",
                action=RecommendedAction.MONITOR_ACCOUNT,
                suggested_investigator_action="No action. Transaction logged for routine periodic review.",
                triggered_by=[],
            ))

        # ----------------------------------------------------------------
        # 2. Supplementary actions based on specific evidence
        # ----------------------------------------------------------------

        # Matched laundering patterns → KYC refresh
        if triggered_patterns:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Refresh Customer KYC",
                description=f"Matched {len(triggered_patterns)} known AML typologies: {', '.join(triggered_patterns)}.",
                priority=_PRIORITY_HIGH,
                reason="Pattern match indicates potential money laundering typology.",
                action=RecommendedAction.ENHANCED_DUE_DILIGENCE,
                suggested_investigator_action=(
                    "Re-verify customer identity documents and source of wealth. "
                    "Update CDD file. Escalate if documents are unavailable."
                ),
                triggered_by=triggered_patterns,
            ))

        # Statistical anomalies → Review historical transactions
        if stat_findings:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Review Historical Transactions",
                description=f"Statistical engine detected {len(stat_findings)} anomalous patterns.",
                priority=_PRIORITY_MEDIUM,
                reason="Statistical deviations from customer baseline behaviour detected.",
                action=RecommendedAction.MONITOR_ACCOUNT,
                suggested_investigator_action=(
                    "Pull 180-day transaction history. Look for structuring, "
                    "round-trip transfers, or velocity increases."
                ),
                triggered_by=[str(f) for f in stat_findings],
            ))

        # Behavioural anomalies → Review related accounts
        if behaviour_findings:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Review Related Accounts",
                description=f"Behaviour Engine identified {len(behaviour_findings)} deviations from customer profile.",
                priority=_PRIORITY_MEDIUM,
                reason="Customer behaviour significantly deviates from established profile.",
                action=RecommendedAction.MONITOR_ACCOUNT,
                suggested_investigator_action=(
                    "Identify linked accounts (joint holders, beneficiaries). "
                    "Check for coordinated suspicious activity across the network."
                ),
                triggered_by=[str(f) for f in behaviour_findings],
            ))

        # ML anomaly → Verify source of funds
        if ml_findings:
            recs.append(Recommendation(
                transaction_id=transaction_id,
                title="Verify Source of Funds",
                description="ML model scored transaction as anomalous.",
                priority=_PRIORITY_HIGH,
                reason=f"ML anomaly score indicates high fraud probability (confidence: {confidence_score:.2f}).",
                action=RecommendedAction.REQUEST_DOCUMENTS,
                suggested_investigator_action=(
                    "Request source of funds declaration from customer. "
                    "Cross-check against declared income and tax records."
                ),
                triggered_by=[str(f) for f in ml_findings],
            ))

        # Sort by priority ascending (1 = most urgent first)
        recs.sort(key=lambda r: r.priority)
        return recs

    @timed("Recommender Batch")
    def recommend_batch(self, risk_df: Any) -> dict[str, List[Recommendation]]:
        """
        Generates Recommendation objects for a batch of transactions.

        Accepts a pandas DataFrame produced from RiskAssessment objects,
        or an empty DataFrame for no-op cases.

        Args:
            risk_df: DataFrame where each row corresponds to a RiskAssessment.
                     Expected columns: transaction_id, customer_id,
                     overall_risk_score, risk_level, confidence_score,
                     triggered_rules, triggered_patterns,
                     supporting_evidence, top_reasons.

        Returns:
            Dict mapping transaction_id → List[Recommendation].
        """
        logger.info("Generating recommendations...")

        if not isinstance(risk_df, pd.DataFrame) or risk_df.empty:
            logger.warning("recommend_batch received empty or invalid risk_df; returning empty dict.")
            return {}

        results: dict[str, List[Recommendation]] = {}

        for _, row in risk_df.iterrows():
            try:
                tid = row.get("transaction_id", "")
                if not tid:
                    continue

                results[tid] = self.recommend(
                    transaction_id=tid,
                    customer_id=row.get("customer_id", ""),
                    risk_score=float(row.get("overall_risk_score", 0.0)),
                    risk_level=str(row.get("risk_level", "LOW")),
                    confidence_score=float(row.get("confidence_score", 0.0)),
                    triggered_rules=row.get("triggered_rules", []) or [],
                    triggered_patterns=row.get("triggered_patterns", []) or [],
                    supporting_evidence=row.get("supporting_evidence", {}) or {},
                    top_reasons=row.get("top_reasons", []) or [],
                )
            except Exception as exc:
                logger.warning("Failed to generate recommendation for row: %s", exc)
                continue

        logger.info("Generated recommendations for %d transactions.", len(results))
        return results
