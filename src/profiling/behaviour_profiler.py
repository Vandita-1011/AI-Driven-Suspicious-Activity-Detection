"""
Behaviour Profiler
==================
Calculates comprehensive historical baseline metrics for customers.
"""
import time
import pandas as pd
from typing import Any

from src.interfaces.base_profiler import BaseBehaviourProfiler
from src.profiling.profile_models import BehaviourProfile
from src.profiling.profile_builder import ProfileBuilder
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BehaviourProfiler(BaseBehaviourProfiler):
    """
    Builds and retrieves comprehensive behaviour profiles based on the enriched transactions dataset.
    """
    def __init__(self, enriched_df: pd.DataFrame) -> None:
        """
        Args:
            enriched_df: The fully enriched transaction history.
        """
        self.df = enriched_df
        self._customer_profiles: dict[str, BehaviourProfile] = {}
        self.builder = ProfileBuilder()

    def build_all_profiles(self) -> None:
        """
        Calculates baselines for all customers using vectorized operations.
        """
        if self.df.empty:
            logger.warning("Empty DataFrame provided to BehaviourProfiler.")
            return

        start_time = time.time()
        logger.info("Profile generation started")
        
        self._customer_profiles = self.builder.build_profiles(self.df)
        
        execution_time = time.time() - start_time
        total_customers = len(self._customer_profiles)
        
        logger.info("Profile completed for %d customers. Execution time: %.2fs", total_customers, execution_time)

    def get_profile(self, entity_id: str) -> BehaviourProfile | None:
        """
        Retrieves a profile for a specific customer.
        """
        return self._customer_profiles.get(str(entity_id))

