"""
Pattern Models
==============
Data models and Enums for the AML Pattern Identification stage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from src.agent.intent_models import IntentResult
from src.agent.entity_models import EntityExtractionResult


class InvestigationPatternType(str, Enum):
    """Supported logical investigation patterns."""
    CUSTOMER_INVESTIGATION = "CUSTOMER_INVESTIGATION"
    TRANSACTION_INVESTIGATION = "TRANSACTION_INVESTIGATION"
    HIGH_RISK_CUSTOMER_REVIEW = "HIGH_RISK_CUSTOMER_REVIEW"
    SUSPICIOUS_TRANSACTION_ANALYSIS = "SUSPICIOUS_TRANSACTION_ANALYSIS"
    LARGE_CASH_TRANSACTION_REVIEW = "LARGE_CASH_TRANSACTION_REVIEW"
    STRUCTURING_INVESTIGATION = "STRUCTURING_INVESTIGATION"
    SMURFING_INVESTIGATION = "SMURFING_INVESTIGATION"
    RAPID_MOVEMENT_INVESTIGATION = "RAPID_MOVEMENT_INVESTIGATION"
    LAYERING_INVESTIGATION = "LAYERING_INVESTIGATION"
    CROSS_BORDER_INVESTIGATION = "CROSS_BORDER_INVESTIGATION"
    SANCTIONS_INVESTIGATION = "SANCTIONS_INVESTIGATION"
    PEP_INVESTIGATION = "PEP_INVESTIGATION"
    COUNTRY_RISK_INVESTIGATION = "COUNTRY_RISK_INVESTIGATION"
    DORMANT_ACCOUNT_INVESTIGATION = "DORMANT_ACCOUNT_INVESTIGATION"
    ACCOUNT_TAKEOVER_INVESTIGATION = "ACCOUNT_TAKEOVER_INVESTIGATION"
    NETWORK_INVESTIGATION = "NETWORK_INVESTIGATION"
    ALERT_EXPLANATION = "ALERT_EXPLANATION"
    RISK_SUMMARY = "RISK_SUMMARY"
    TOP_N_INVESTIGATION = "TOP_N_INVESTIGATION"
    GENERAL_SEARCH = "GENERAL_SEARCH"
    CUSTOM_INVESTIGATION = "CUSTOM_INVESTIGATION"


class ConfidenceLevel(str, Enum):
    """Categorized confidence levels for planning constraints."""
    HIGH = "HIGH"       # >= 0.90
    MEDIUM = "MEDIUM"   # 0.75 - 0.89
    LOW = "LOW"         # < 0.75


@dataclass
class PatternIdentificationResult:
    """
    Richer result of pattern identification containing all context
    required by the Dynamic Planner.
    """
    investigation_pattern: InvestigationPatternType
    confidence_score: float
    confidence_level: ConfidenceLevel
    reasoning: str
    matched_intent: IntentResult
    matched_entities: EntityExtractionResult
    required_entities: List[str] = field(default_factory=list)
    missing_entities: List[str] = field(default_factory=list)
    validation_messages: List[str] = field(default_factory=list)
