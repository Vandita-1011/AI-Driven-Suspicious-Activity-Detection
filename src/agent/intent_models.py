"""
Intent Models
=============
Shared data models for the Intent Recognition module.

Kept in a dedicated file so that downstream modules (entity extractor,
planner, routing) can import Intent and IntentResult without importing
the full recognizer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Intent(str, Enum):
    """
    All supported analyst intents.

    String value is the canonical identifier used in downstream routing.
    """
    DATASET_ANALYSIS = "DATASET_ANALYSIS"
    AML_PATTERN_SEARCH = "AML_PATTERN_SEARCH"
    HIGH_RISK_CUSTOMER = "HIGH_RISK_CUSTOMER"
    CUSTOMER_INVESTIGATION = "CUSTOMER_INVESTIGATION"
    TRANSACTION_INVESTIGATION = "TRANSACTION_INVESTIGATION"
    DASHBOARD_SUMMARY = "DASHBOARD_SUMMARY"
    REPORT_GENERATION = "REPORT_GENERATION"
    UNKNOWN = "UNKNOWN"


@dataclass
class IntentResult:
    """
    Result of a single intent recognition pass.

    Attributes:
        intent:           Detected Intent enum member.
        confidence:       Score in [0.0, 1.0].  Higher means more certain.
                          0.0 indicates UNKNOWN / no match.
        matched_phrases:  The keyword group(s) that drove the decision.
        raw_query:        The original (un-normalised) query string.
        normalized_query: The normalised form used for matching.
    """
    intent: Intent
    confidence: float
    matched_phrases: List[str]
    raw_query: str
    normalized_query: str
