"""
AML Scenario Constants
======================
Defines all 15 AML scenario tags as a typed Enum.

These tags match EXACTLY the values written into the dataset's
``aml_scenario_tag`` column by the synthetic data generator.

Do NOT change these string values — they are the ground-truth labels
baked into every row of transaction.csv.

Money-laundering operates in three classic stages:
  - Placement  : introducing illegal cash into the financial system
  - Layering   : obscuring the origin through complex transactions
  - Integration: re-entering funds as apparently legitimate money

The 15 scenarios span all three stages.
"""
from enum import Enum


class AMLScenario(str, Enum):
    """
    Enumeration of all 15 AML scenario tags present in the dataset.

    Each member's value is the exact string stored in the
    ``aml_scenario_tag`` column of ``transaction.csv``.

    Using this Enum throughout the codebase prevents typos and
    enables IDE auto-completion for scenario names.
    """

    # ── Placement-stage ─────────────────────────────────────────────────
    STRUCTURING = "Structuring"
    """Multiple deposits just below the reporting threshold in a short window."""

    SMURFING = "Smurfing"
    """Many different senders depositing small amounts into one target account."""

    ROUND_AMOUNT = "Round-Amount"
    """Suspiciously exact round-number transactions (e.g. 10 000, 50 000)."""

    # ── Layering-stage ──────────────────────────────────────────────────
    LAYERING = "Layering"
    """Multi-hop transfer chain (A → B → C → D) to obscure fund origin."""

    CIRCULAR = "Circular"
    """Circular fund flow: A → B → C → A, money returns to origin."""

    MULE_ACCOUNTS = "Mule Accounts"
    """Rapid pass-through: large credit immediately followed by near-full debit."""

    SHELL_COMPANIES = "Shell Companies"
    """Business/Corporate accounts with only pass-through activity."""

    DORMANT_ACTIVATION = "Dormant Activation"
    """Dormant account suddenly reactivated with an unusually large transaction."""

    VELOCITY_ANOMALIES = "Velocity Anomalies"
    """Abnormally high transaction count within a short time window."""

    TRANSACTION_BURSTS = "Transaction Bursts"
    """Sudden burst of many transactions within a single day."""

    RELATIONSHIP_BASED = "Relationship-Based"
    """Structuring spread across related customers to stay under thresholds."""

    # ── Integration-stage ───────────────────────────────────────────────
    INTEGRATION = "Integration"
    """Final-stage large 'legitimate-looking' purchase or investment."""

    HIGH_RISK_GEOGRAPHY = "High-Risk Geography"
    """Transfers to/from FATF grey/black-listed jurisdictions."""

    CROSS_BORDER_UNUSUAL = "Cross-Border Unusual"
    """Cross-border transaction inconsistent with the customer's normal profile."""

    TBML = "TBML"
    """Trade-Based Money Laundering: round-number invoice payments to trade merchants."""

    # ── Class-level helpers ─────────────────────────────────────────────

    @classmethod
    def all_tags(cls) -> list[str]:
        """Returns all 15 scenario tag strings as a plain list.

        Returns:
            List of scenario value strings in definition order.
        """
        return [scenario.value for scenario in cls]

    @classmethod
    def placement_stage(cls) -> list["AMLScenario"]:
        """Returns placement-stage scenarios."""
        return [cls.STRUCTURING, cls.SMURFING, cls.ROUND_AMOUNT]

    @classmethod
    def layering_stage(cls) -> list["AMLScenario"]:
        """Returns layering-stage scenarios."""
        return [
            cls.LAYERING, cls.CIRCULAR, cls.MULE_ACCOUNTS,
            cls.SHELL_COMPANIES, cls.DORMANT_ACTIVATION,
            cls.VELOCITY_ANOMALIES, cls.TRANSACTION_BURSTS,
            cls.RELATIONSHIP_BASED,
        ]

    @classmethod
    def integration_stage(cls) -> list["AMLScenario"]:
        """Returns integration-stage scenarios."""
        return [
            cls.INTEGRATION, cls.HIGH_RISK_GEOGRAPHY,
            cls.CROSS_BORDER_UNUSUAL, cls.TBML,
        ]

    @classmethod
    def from_tag(cls, tag: str | None) -> "AMLScenario | None":
        """Safe lookup: returns matching AMLScenario or None.

        Args:
            tag: Raw string from the ``aml_scenario_tag`` column.
                 May be None (for Normal transactions).

        Returns:
            Matching AMLScenario member, or None if not found.
        """
        if tag is None:
            return None
        for scenario in cls:
            if scenario.value == tag:
                return scenario
        return None


class FlagLabel(str, Enum):
    """
    Values present in the ``flag_label`` column of transaction.csv.

    Used as the ground-truth label for model evaluation and for filtering
    suspicious transactions during analysis.
    """
    NORMAL = "Normal"
    SUSPICIOUS = "Suspicious"
