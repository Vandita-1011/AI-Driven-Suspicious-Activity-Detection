"""
Base Profiler Interface
=======================
Defines the contract for behaviour profiling.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class BehaviourProfile:
    """
    Represents a customer's or account's historical behaviour baseline.
    """
    entity_id: str
    entity_type: str  # e.g., 'customer', 'account'
    features: dict[str, Any] = field(default_factory=dict)
    
    # E.g., avg_txn_amount, typical_hour_of_day, preferred_channel, etc.


class BaseBehaviourProfiler(ABC):
    """
    Abstract base class for behaviour profilers.
    """

    @abstractmethod
    def build_all_profiles(self) -> None:
        """
        Builds behaviour profiles for all entities based on historical data.
        """
        pass

    @abstractmethod
    def get_profile(self, entity_id: str) -> BehaviourProfile | None:
        """
        Retrieves the behaviour profile for a specific entity.

        Args:
            entity_id: The ID of the customer or account.

        Returns:
            The BehaviourProfile, or None if no history exists.
        """
        pass
