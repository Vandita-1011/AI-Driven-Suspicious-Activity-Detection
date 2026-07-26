"""
Constants Package
=================
All project-wide string constants, enumerations and typed identifiers.

Sub-modules:
    aml_scenarios   AMLScenario enum (15 tags), FlagLabel enum
    column_names    Per-table column name classes (TxnCols, CustomerCols …)
    risk_levels     RiskLevel, AlertPriority, FATFStatus and other enums

Usage:
    from src.constants.aml_scenarios import AMLScenario
    from src.constants.column_names import TxnCols, CustomerCols
    from src.constants.risk_levels import RiskLevel, AlertPriority
"""
from src.constants.aml_scenarios import AMLScenario, FlagLabel
from src.constants.column_names import (
    TxnCols, CustomerCols, AccountCols, DeviceCols, BeneficiaryCols,
    MerchantCols, LocationCols, BranchCols, CountryRiskCols,
    RelationshipCols, FraudRingCols, FraudRingMembershipCols, ComputedCols,
)
from src.constants.risk_levels import (
    RiskLevel, AlertPriority, FATFStatus, ProfileSegment,
    KYCLevel, AccountStatus, TransactionType, Channel, RecommendedAction,
)

__all__ = [
    "AMLScenario", "FlagLabel",
    "TxnCols", "CustomerCols", "AccountCols", "DeviceCols", "BeneficiaryCols",
    "MerchantCols", "LocationCols", "BranchCols", "CountryRiskCols",
    "RelationshipCols", "FraudRingCols", "FraudRingMembershipCols", "ComputedCols",
    "RiskLevel", "AlertPriority", "FATFStatus", "ProfileSegment",
    "KYCLevel", "AccountStatus", "TransactionType", "Channel", "RecommendedAction",
]
