"""
Risk Level Constants
====================
Enumerations for risk tiers, alert priorities, FATF statuses, customer
segments, and all other categorical domain values used throughout the
AI engine.

Rules:
  - Use these Enums everywhere — never hardcode the string values.
  - String values match exactly what the generator writes to CSV.
"""
from enum import Enum


class RiskLevel(str, Enum):
    """
    Four-tier risk classification for transactions and customers.

    Maps to numeric fused_risk_score ranges defined in engine_config.yaml
    under ``risk_fusion.risk_thresholds``.

    Default mapping:
        LOW      :   0 – 24
        MEDIUM   :  25 – 49
        HIGH     :  50 – 74
        CRITICAL :  75 – 100
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_score(cls, score: float, thresholds: dict[str, int]) -> "RiskLevel":
        """Converts a numeric risk score [0–100] to a RiskLevel.

        Args:
            score: Numeric risk score (float, clamped to 0–100).
            thresholds: Dict with keys ``critical``, ``high``, ``medium``
                        sourced from engine_config.yaml.

        Returns:
            Corresponding RiskLevel enum member.
        """
        if score >= thresholds.get("critical", 90):
            return cls.CRITICAL
        elif score >= thresholds.get("high", 75):
            return cls.HIGH
        elif score >= thresholds.get("medium", 50):
            return cls.MEDIUM
        else:
            return cls.LOW

    @property
    def numeric_order(self) -> int:
        """Returns a sortable integer (higher = more severe)."""
        return {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}[self.value]


class AlertPriority(str, Enum):
    """
    Alert priority levels used by the AlertPrioritizer.

    Maps one-to-one with RiskLevel, using P1–P4 naming for clarity
    in alert dashboards and reporting.
    """
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"

    @classmethod
    def from_risk_level(cls, risk_level: "RiskLevel") -> "AlertPriority":
        """Maps a RiskLevel to the corresponding AlertPriority.

        Args:
            risk_level: Source RiskLevel.

        Returns:
            Matching AlertPriority.
        """
        mapping: dict[RiskLevel, "AlertPriority"] = {
            RiskLevel.CRITICAL: cls.P1_CRITICAL,
            RiskLevel.HIGH: cls.P2_HIGH,
            RiskLevel.MEDIUM: cls.P3_MEDIUM,
            RiskLevel.LOW: cls.P4_LOW,
        }
        return mapping[risk_level]

    @property
    def numeric_order(self) -> int:
        """Returns a sortable integer (higher = more urgent)."""
        return {
            "P4_LOW": 0, "P3_MEDIUM": 1,
            "P2_HIGH": 2, "P1_CRITICAL": 3,
        }[self.value]


class FATFStatus(str, Enum):
    """
    FATF jurisdiction risk status values.

    Matches the ``fatf_status`` column values in ``country_risk.csv``.
    """
    NORMAL = "Normal"
    """Low-risk jurisdiction — standard due diligence."""

    GREY = "Grey"
    """FATF Grey List — enhanced monitoring required."""

    BLACK = "Black"
    """FATF Black List (Blacklisted) — highest risk, near-total sanctions."""

    @property
    def risk_weight(self) -> float:
        """Returns a numeric weight for risk scoring."""
        return {"Normal": 0.1, "Grey": 0.6, "Black": 1.0}[self.value]


class ProfileSegment(str, Enum):
    """Customer profile segment values from ``customer.csv``."""
    RETAIL = "Retail"
    HNI = "HNI"
    CORPORATE = "Corporate"
    BUSINESS = "Business"
    STUDENT = "Student"
    RETIREE = "Retiree"

    @property
    def expected_avg_amount(self) -> float:
        """Returns the segment's expected average transaction amount (INR).
        Matches the generator's mean_amt mapping."""
        return {
            "Retail": 8_000.0,
            "HNI": 60_000.0,
            "Corporate": 150_000.0,
            "Business": 90_000.0,
            "Student": 1_500.0,
            "Retiree": 5_000.0,
        }[self.value]


class KYCLevel(str, Enum):
    """KYC risk levels from the ``kyc_level`` column in ``customer.csv``."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    @property
    def risk_weight(self) -> float:
        """Returns a numeric weight for KYC-based risk scoring."""
        return {"Low": 0.3, "Medium": 0.6, "High": 1.0}[self.value]


class AccountStatus(str, Enum):
    """Account status values from the ``status`` column in ``account.csv``."""
    ACTIVE = "Active"
    DORMANT = "Dormant"


class TransactionType(str, Enum):
    """Transaction type values from the ``transaction_type`` column."""
    CREDIT = "Credit"
    DEBIT = "Debit"
    TRANSFER = "Transfer"
    POS = "POS"
    ATM = "ATM"

    @property
    def is_debit(self) -> bool:
        """True for transaction types that reduce the account balance."""
        return self in (self.DEBIT, self.ATM, self.POS, self.TRANSFER)


class Channel(str, Enum):
    """Transaction channel values from the ``channel`` column."""
    ONLINE = "Online"
    BRANCH = "Branch"
    ATM = "ATM"
    POS = "POS"


class FraudRingRole(str, Enum):
    """
    Member roles within a fraud ring.
    Values match the ``role`` column in ``customer_fraud_ring_membership.csv``.
    """
    LEADER = "Leader"
    MULE = "Mule"
    MEMBER = "Member"


class RecommendedAction(str, Enum):
    """
    Investigator action recommendations produced by the Recommender.

    Ordered from most to least severe:
        FILE_SAR           → CRITICAL risk / multiple pattern matches
        FREEZE_ACCOUNT     → CRITICAL with active fraud ring involvement
        ESCALATE           → HIGH risk with PEP / sanctions flag
        ENHANCED_DD        → HIGH risk without PEP / sanctions
        REQUEST_DOCUMENTS  → MEDIUM risk requiring evidence
        MONITOR_ACCOUNT    → MEDIUM risk, ongoing surveillance
        ROUTINE_REVIEW     → LOW risk, periodic check
        NO_ACTION          → Clean transaction
    """
    FILE_SAR = "File Suspicious Activity Report (SAR)"
    FREEZE_ACCOUNT = "Freeze Account for Review"
    ESCALATE_TO_COMPLIANCE = "Escalate to Compliance Officer"
    ENHANCED_DUE_DILIGENCE = "Enhanced Due Diligence (EDD)"
    REQUEST_DOCUMENTS = "Request Supporting Documents from Customer"
    MONITOR_ACCOUNT = "Place Account Under Enhanced Monitoring"
    ROUTINE_REVIEW = "Routine Periodic Review"
    NO_ACTION = "No Action Required"
