"""
Entity Models
=============
Shared data models for the Entity & Filter Extraction module.

Kept separate so downstream modules (planner, routing) can import
only the types without pulling in extraction logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RiskLevelFilter(str, Enum):
    """Normalised risk level filters extracted from analyst queries."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AmountOperator(str, Enum):
    """Comparison operator for an amount filter."""
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    BETWEEN = "BETWEEN"
    EQUALS = "EQUALS"


@dataclass
class AmountFilter:
    """
    A monetary amount constraint extracted from the query.

    Examples::

        "above 100000"      → AmountFilter(operator=ABOVE, value=100000.0)
        "less than 50000"   → AmountFilter(operator=BELOW, value=50000.0)
        "between 10k and 50k" → AmountFilter(operator=BETWEEN,
                                             value=10000.0, upper=50000.0)
    """
    operator: AmountOperator
    value: float
    upper: Optional[float] = None       # populated only for BETWEEN


@dataclass
class DateFilter:
    """
    A temporal constraint extracted from the query.

    Attributes:
        label:      Human-readable label (e.g. "last_30_days", "today").
        start_date: ISO-format date string or None when relative.
        end_date:   ISO-format date string or None when relative.
    """
    label: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class EntityExtractionResult:
    """
    Structured entities and filters extracted from a single analyst query.

    All list fields default to empty lists rather than None so downstream
    consumers can iterate without defensive checks.

    Attributes:
        customer_ids:     Extracted customer ID strings (e.g. ["4521", "C1001"]).
        transaction_ids:  Extracted transaction ID strings (e.g. ["TX102"]).
        account_ids:      Extracted account ID strings (e.g. ["A100"]).
        risk_level:       Optional normalised risk level filter.
        aml_patterns:     Matched AML typology names.
        countries:        Extracted country names.
        amount_filters:   Amount constraints (there may be several).
        date_filter:      Optional temporal constraint.
        limit:            Top-N limit extracted from the query (e.g. 10).
        raw_query:        The original (un-normalised) query string.
        remaining_text:   Query text after all entities have been removed.
    """
    customer_ids: List[str] = field(default_factory=list)
    transaction_ids: List[str] = field(default_factory=list)
    account_ids: List[str] = field(default_factory=list)
    risk_level: Optional[RiskLevelFilter] = None
    aml_patterns: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    amount_filters: List[AmountFilter] = field(default_factory=list)
    date_filter: Optional[DateFilter] = None
    limit: Optional[int] = None
    raw_query: str = ""
    remaining_text: str = ""
