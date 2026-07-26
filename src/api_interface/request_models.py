"""
API Request Models
==================
Typed plain Python dataclasses representing API requests.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnalysisRequest:
    """Request to run the full detection pipeline."""
    run_id: str
    filter_date_start: Optional[str] = None
    filter_date_end: Optional[str] = None


@dataclass
class CustomerQueryRequest:
    """Request to query a specific customer's risk profile."""
    customer_id: str
    include_transactions: bool = False


@dataclass
class AlertQueryRequest:
    """Request to fetch generated alerts."""
    min_priority: str = "P4_LOW"
    limit: int = 100
    offset: int = 0
