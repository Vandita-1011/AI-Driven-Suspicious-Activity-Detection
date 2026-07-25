import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np
from typing import Dict, List, Optional, Any

from src.constants.column_names import TxnCols, CustomerCols, ComputedCols
from src.profiling.profile_models import BehaviourProfile
from src.features.feature_models import FeatureVector
from src.utils.logger import get_logger
from src.exceptions.engine_exceptions import PreprocessingError

logger = get_logger(__name__)


class FeatureBuilder:
    """
    Builds transaction-level core feature vectors using vectorized Pandas operations.
    """

    def build_features(
        self, 
        enriched_df: pd.DataFrame, 
        profiles: Optional[Dict[str, BehaviourProfile]] = None
    ) -> pd.DataFrame:
        """
        Calculates Amount, Velocity, and Behaviour Deviation features for all transactions.

        Args:
            enriched_df: Cleaned and enriched transaction DataFrame.
            profiles: Map of customer_id -> BehaviourProfile.

        Returns:
            DataFrame containing all engineered feature columns alongside key IDs.
        """
        if enriched_df.empty:
            logger.warning("Empty DataFrame provided to FeatureBuilder.")
            return pd.DataFrame()

        logger.info("Computing core features for %d transactions...", len(enriched_df))
        df = enriched_df.copy()

        # Ensure timestamps are sorted per customer for accurate velocity calculations
        if TxnCols.TIMESTAMP in df.columns:
            df[TxnCols.TIMESTAMP] = pd.to_datetime(df[TxnCols.TIMESTAMP], utc=True)
            df = df.sort_values(by=[TxnCols.CUSTOMER_ID, TxnCols.TIMESTAMP]).reset_index(drop=True)

        # 1. Compute Amount Features
        df = self._compute_amount_features(df, profiles)

        # 2. Compute Velocity Features
        df = self._compute_velocity_features(df)

        # 3. Compute Behaviour Deviation Features
        df = self._compute_behaviour_features(df, profiles)

        logger.info("Core feature engineering completed successfully.")
        return df

    def _compute_amount_features(
        self, 
        df: pd.DataFrame, 
        profiles: Optional[Dict[str, BehaviourProfile]]
    ) -> pd.DataFrame:
        logger.debug("Computing amount features...")
        amt_col = TxnCols.AMOUNT if TxnCols.AMOUNT in df.columns else 'amount'
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in df.columns else 'customer_id'

        # Default fallback aggregations from the DataFrame if profile is not provided
        grouped = df.groupby(cust_col)[amt_col]
        cust_avg = grouped.transform('mean')
        cust_median = grouped.transform('median')
        cust_std = grouped.transform('std').fillna(0.0)
        cust_max = grouped.transform('max')
        cust_min = grouped.transform('min')

        # Override with profile statistics if available
        if profiles:
            def _get_prof_stat(cust_id: Any, stat_name: str, fallback: float) -> float:
                p = profiles.get(str(cust_id))
                if p and hasattr(p, 'statistics'):
                    return getattr(p.statistics, stat_name, fallback)
                return fallback

            # Create mappings for profiles
            avg_map = {cid: p.statistics.avg_amount for cid, p in profiles.items() if hasattr(p, 'statistics')}
            med_map = {cid: p.statistics.median_amount for cid, p in profiles.items() if hasattr(p, 'statistics')}
            std_map = {cid: p.statistics.std_amount for cid, p in profiles.items() if hasattr(p, 'statistics')}
            max_map = {cid: p.statistics.max_amount for cid, p in profiles.items() if hasattr(p, 'statistics')}
            min_map = {cid: p.statistics.min_amount for cid, p in profiles.items() if hasattr(p, 'statistics')}

            cust_avg = df[cust_col].astype(str).map(avg_map).fillna(cust_avg)
            cust_median = df[cust_col].astype(str).map(med_map).fillna(cust_median)
            cust_std = df[cust_col].astype(str).map(std_map).fillna(cust_std)
            cust_max = df[cust_col].astype(str).map(max_map).fillna(cust_max)
            cust_min = df[cust_col].astype(str).map(min_map).fillna(cust_min)

        df['transaction_amount'] = df[amt_col].astype(float)
        df['customer_average_amount'] = cust_avg.astype(float)
        df['customer_median_amount'] = cust_median.astype(float)
        df['customer_std_amount'] = cust_std.astype(float)
        df['historical_max_amount'] = cust_max.astype(float)
        df['historical_min_amount'] = cust_min.astype(float)

        df['amount_difference'] = df['transaction_amount'] - df['customer_average_amount']
        df['amount_ratio_to_average'] = df['transaction_amount'] / (df['customer_average_amount'] + 1e-5)
        df['amount_z_score'] = df['amount_difference'] / (df['customer_std_amount'] + 1e-5)

        # Percentile rank per customer
        df['amount_percentile'] = grouped.rank(pct=True).astype(float)
        df['large_transaction_flag'] = (
            (df['amount_z_score'] > 3.0) | (df['transaction_amount'] > 3.0 * df['customer_average_amount'])
        ).astype(bool)

        return df

    def _compute_velocity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Computing velocity features...")
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in df.columns else 'customer_id'
        ts_col = TxnCols.TIMESTAMP if TxnCols.TIMESTAMP in df.columns else 'timestamp'
        amt_col = TxnCols.AMOUNT if TxnCols.AMOUNT in df.columns else 'amount'

        # Time since previous transaction (in hours)
        df['prev_timestamp'] = df.groupby(cust_col)[ts_col].shift(1)
        df['time_since_previous_transaction'] = (
            (df[ts_col] - df['prev_timestamp']).dt.total_seconds() / 3600.0
        ).fillna(0.0).astype(float)
        df.drop(columns=['prev_timestamp'], inplace=True)

        # Rolling calculations using time-indexed rolling per customer
        # We process each customer subgroup to compute exact time window counts/sums
        results_list = []
        for _, group in df.groupby(cust_col, sort=False):
            g = group.set_index(ts_col)
            
            # Last 1 hour
            g['transactions_last_hour'] = g[amt_col].rolling('1h').count().astype(int)
            # Last 24 hours
            g['transactions_last_day'] = g[amt_col].rolling('24h').count().astype(int)
            g['amount_last_day'] = g[amt_col].rolling('24h').sum().astype(float)
            # Last 7 days
            g['transactions_last_week'] = g[amt_col].rolling('7d').count().astype(int)
            g['amount_last_week'] = g[amt_col].rolling('7d').sum().astype(float)
            
            # Rolling window stats (24h)
            g['rolling_transaction_count'] = g['transactions_last_day']
            g['rolling_average_amount'] = g[amt_col].rolling('24h').mean().astype(float)
            g['rolling_std_amount'] = g[amt_col].rolling('24h').std().fillna(0.0).astype(float)
            
            # Average gap between transactions (rolling mean of gap over last 7d)
            g['average_gap_between_transactions'] = (
                g['time_since_previous_transaction'].rolling('7d').mean().fillna(0.0).astype(float)
            )
            
            results_list.append(g.reset_index())

        velocity_df = pd.concat(results_list, ignore_index=True)
        return velocity_df

    def _compute_behaviour_features(
        self, 
        df: pd.DataFrame, 
        profiles: Optional[Dict[str, BehaviourProfile]]
    ) -> pd.DataFrame:
        logger.debug("Computing behaviour deviation features...")
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in df.columns else 'customer_id'
        
        # Determine business hours flag
        if 'is_business_hours' in df.columns:
            df['outside_business_hours'] = ~df['is_business_hours'].astype(bool)
        elif ComputedCols.HOUR_OF_DAY in df.columns:
            df['outside_business_hours'] = ~df[ComputedCols.HOUR_OF_DAY].between(9, 17)
        else:
            df['outside_business_hours'] = False

        pref_hour_map = {}
        pref_wday_map = {}
        pref_month_map = {}
        daily_freq_map = {}

        if profiles:
            for cid, p in profiles.items():
                if hasattr(p, 'statistics'):
                    pref_hour_map[cid] = p.statistics.preferred_hour
                    pref_wday_map[cid] = p.statistics.most_active_weekday
                    pref_month_map[cid] = p.statistics.most_active_month
                    daily_freq_map[cid] = p.statistics.avg_daily_txns

        curr_hour = df[ComputedCols.HOUR_OF_DAY] if ComputedCols.HOUR_OF_DAY in df.columns else df[TxnCols.TIMESTAMP].dt.hour
        curr_wday = df[ComputedCols.DAY_OF_WEEK] if ComputedCols.DAY_OF_WEEK in df.columns else df[TxnCols.TIMESTAMP].dt.dayofweek
        curr_month = df['transaction_month'] if 'transaction_month' in df.columns else df[TxnCols.TIMESTAMP].dt.month

        pref_hour = df[cust_col].astype(str).map(pref_hour_map).fillna(curr_hour)
        pref_wday = df[cust_col].astype(str).map(pref_wday_map).fillna(curr_wday)
        pref_month = df[cust_col].astype(str).map(pref_month_map).fillna(curr_month)
        avg_daily = df[cust_col].astype(str).map(daily_freq_map).fillna(1.0)

        df['outside_preferred_hour'] = (curr_hour != pref_hour).astype(bool)
        df['unusual_weekday'] = (curr_wday != pref_wday).astype(bool)
        df['unusual_month'] = (curr_month != pref_month).astype(bool)

        # Deviation Scores
        df['amount_deviation_score'] = df['amount_z_score'].abs().clip(lower=0.0, upper=5.0) / 5.0
        df['frequency_deviation_score'] = (
            (df['transactions_last_day'] / (avg_daily + 1e-5)).clip(lower=0.0, upper=5.0) / 5.0
        )

        # Weighted aggregate behaviour deviation score (0.0 to 1.0)
        df['behaviour_deviation_score'] = (
            0.4 * df['amount_deviation_score'] +
            0.3 * df['frequency_deviation_score'] +
            0.1 * df['outside_business_hours'].astype(float) +
            0.1 * df['outside_preferred_hour'].astype(float) +
            0.1 * df['unusual_weekday'].astype(float)
        ).clip(lower=0.0, upper=1.0).astype(float)

        return df

    def to_feature_vectors(self, feature_df: pd.DataFrame) -> List[FeatureVector]:
        """Converts a feature DataFrame into a list of strongly-typed FeatureVector dataclasses."""
        vectors = []
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in feature_df.columns else 'customer_id'
        acc_col = TxnCols.ACCOUNT_ID if TxnCols.ACCOUNT_ID in feature_df.columns else 'account_id'
        txn_col = TxnCols.TRANSACTION_ID if TxnCols.TRANSACTION_ID in feature_df.columns else 'transaction_id'
        ts_col = TxnCols.TIMESTAMP if TxnCols.TIMESTAMP in feature_df.columns else 'timestamp'

        for row in feature_df.to_dict(orient='records'):
            vector = FeatureVector(
                transaction_id=str(row.get(txn_col, '')),
                customer_id=str(row.get(cust_col, '')),
                account_id=str(row.get(acc_col, '')),
                timestamp=row.get(ts_col),

                transaction_amount=float(row.get('transaction_amount', 0.0)),
                customer_average_amount=float(row.get('customer_average_amount', 0.0)),
                customer_median_amount=float(row.get('customer_median_amount', 0.0)),
                customer_std_amount=float(row.get('customer_std_amount', 0.0)),
                amount_difference=float(row.get('amount_difference', 0.0)),
                amount_ratio_to_average=float(row.get('amount_ratio_to_average', 0.0)),
                amount_z_score=float(row.get('amount_z_score', 0.0)),
                amount_percentile=float(row.get('amount_percentile', 0.0)),
                historical_max_amount=float(row.get('historical_max_amount', 0.0)),
                historical_min_amount=float(row.get('historical_min_amount', 0.0)),
                large_transaction_flag=bool(row.get('large_transaction_flag', False)),

                transactions_last_hour=int(row.get('transactions_last_hour', 0)),
                transactions_last_day=int(row.get('transactions_last_day', 0)),
                transactions_last_week=int(row.get('transactions_last_week', 0)),
                amount_last_day=float(row.get('amount_last_day', 0.0)),
                amount_last_week=float(row.get('amount_last_week', 0.0)),
                rolling_transaction_count=int(row.get('rolling_transaction_count', 0)),
                rolling_average_amount=float(row.get('rolling_average_amount', 0.0)),
                rolling_std_amount=float(row.get('rolling_std_amount', 0.0)),
                average_gap_between_transactions=float(row.get('average_gap_between_transactions', 0.0)),
                time_since_previous_transaction=float(row.get('time_since_previous_transaction', 0.0)),

                outside_business_hours=bool(row.get('outside_business_hours', False)),
                outside_preferred_hour=bool(row.get('outside_preferred_hour', False)),
                unusual_weekday=bool(row.get('unusual_weekday', False)),
                unusual_month=bool(row.get('unusual_month', False)),
                amount_deviation_score=float(row.get('amount_deviation_score', 0.0)),
                frequency_deviation_score=float(row.get('frequency_deviation_score', 0.0)),
                behaviour_deviation_score=float(row.get('behaviour_deviation_score', 0.0))
            )
            vectors.append(vector)
        return vectors
