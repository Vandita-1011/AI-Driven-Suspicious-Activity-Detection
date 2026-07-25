"""
Behaviour Profiler
==================
Calculates historical baseline metrics for customers and accounts.
"""
from typing import Any

import pandas as pd

from src.constants.column_names import ComputedCols, TxnCols
from src.interfaces.base_profiler import BaseBehaviourProfiler, BehaviourProfile
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


class BehaviourProfiler(BaseBehaviourProfiler):
    """
    Builds and retrieves behaviour profiles based on the enriched transactions dataset.
    """

    def __init__(self, enriched_df: pd.DataFrame) -> None:
        """
        Args:
            enriched_df: The fully enriched transaction history.
        """
        self.df = enriched_df
        self._customer_profiles: dict[str, BehaviourProfile] = {}
        self._account_profiles: dict[str, BehaviourProfile] = {}

    @timed("Behaviour Profiling")
    def build_all_profiles(self) -> None:
        """
        Calculates baselines for all customers and accounts.
        """
        if self.df.empty:
            logger.warning("Empty DataFrame provided to BehaviourProfiler.")
            return

        logger.info("Building customer and account behaviour profiles...")

        # 1. Customer Profiles (e.g., avg amount, preferred channel)
        if TxnCols.CUSTOMER_ID in self.df.columns:
            cust_grouped = self.df.groupby(TxnCols.CUSTOMER_ID)
            
            avg_amounts = cust_grouped[TxnCols.AMOUNT].mean()
            tx_counts = cust_grouped.size()
            
            for cust_id in avg_amounts.index:
                self._customer_profiles[str(cust_id)] = BehaviourProfile(
                    entity_id=str(cust_id),
                    entity_type="customer",
                    features={
                        "avg_amount": float(avg_amounts[cust_id]),
                        "total_transactions": int(tx_counts[cust_id]),
                        # Add other aggregations (e.g., preferred channel via mode) as needed
                    }
                )

        # 2. Account Profiles
        if TxnCols.ACCOUNT_ID in self.df.columns:
            acc_grouped = self.df.groupby(TxnCols.ACCOUNT_ID)
            
            acc_avg_amounts = acc_grouped[TxnCols.AMOUNT].mean()
            acc_tx_counts = acc_grouped.size()
            
            for acc_id in acc_avg_amounts.index:
                self._account_profiles[str(acc_id)] = BehaviourProfile(
                    entity_id=str(acc_id),
                    entity_type="account",
                    features={
                        "avg_amount": float(acc_avg_amounts[acc_id]),
                        "total_transactions": int(acc_tx_counts[acc_id]),
                    }
                )

        logger.info("Built %d customer profiles and %d account profiles.", 
                    len(self._customer_profiles), len(self._account_profiles))

    def get_profile(self, entity_id: str) -> BehaviourProfile | None:
        """
        Retrieves a profile (checks customers first, then accounts).
        """
        if entity_id in self._customer_profiles:
            return self._customer_profiles[entity_id]
        if entity_id in self._account_profiles:
            return self._account_profiles[entity_id]
        return None
