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

        # 4. Compute Relationship Features
        df = self._compute_relationship_features(df)

        # 5. Compute Device Features
        df = self._compute_device_features(df)

        # 6. Compute Channel Features
        df = self._compute_channel_features(df, profiles)

        # 7. Compute Geographic Features
        df = self._compute_geographic_features(df, profiles)

        # 8. Compute Historical Features
        df = self._compute_historical_features(df, profiles)

        logger.info("Advanced feature engineering completed successfully.")
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

    def _compute_relationship_features(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Computing relationship features...")
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in df.columns else 'customer_id'
        ben_col = TxnCols.COUNTERPARTY_ACCOUNT_ID if TxnCols.COUNTERPARTY_ACCOUNT_ID in df.columns else 'counterparty_account_id'
        amt_col = TxnCols.AMOUNT if TxnCols.AMOUNT in df.columns else 'amount'

        if ben_col in df.columns:
            # First occurrence per customer-beneficiary pair
            cum_count = df.groupby([cust_col, ben_col]).cumcount()
            df['new_beneficiary'] = (cum_count == 0).astype(bool)
            df['beneficiary_frequency'] = (cum_count + 1).astype(int)
            df['beneficiary_transaction_count'] = df.groupby([cust_col, ben_col])[ben_col].transform('count').astype(int)

            # Cumulative stats per beneficiary
            df['beneficiary_amount_average'] = df.groupby([cust_col, ben_col])[amt_col].transform('mean').astype(float)
            df['beneficiary_amount_std'] = df.groupby([cust_col, ben_col])[amt_col].transform('std').fillna(0.0).astype(float)
            df['beneficiary_is_high_frequency'] = (df['beneficiary_transaction_count'] > 10).astype(bool)
        else:
            df['new_beneficiary'] = False
            df['beneficiary_frequency'] = 1
            df['beneficiary_amount_average'] = df[amt_col].astype(float)
            df['beneficiary_amount_std'] = 0.0
            df['beneficiary_transaction_count'] = 1
            df['beneficiary_is_high_frequency'] = False

        return df

    def _compute_device_features(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Computing device features...")
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in df.columns else 'customer_id'
        dev_col = TxnCols.DEVICE_ID if TxnCols.DEVICE_ID in df.columns else 'device_id'
        ts_col = TxnCols.TIMESTAMP if TxnCols.TIMESTAMP in df.columns else 'timestamp'

        if dev_col in df.columns:
            cum_dev_count = df.groupby([cust_col, dev_col]).cumcount()
            df['new_device'] = (cum_dev_count == 0).astype(bool)
            df['device_frequency'] = (cum_dev_count + 1).astype(int)

            # Device switch flag (different from previous transaction's device)
            prev_device = df.groupby(cust_col)[dev_col].shift(1)
            df['device_switch_flag'] = (df[dev_col] != prev_device) & prev_device.notna()

            # Unique devices in rolling 30-day window per customer
            unique_dev_list = []
            for _, group in df.groupby(cust_col, sort=False):
                g = group.set_index(ts_col)
                # Count unique device_ids in trailing 30d window
                g['unique_devices_last_30_days'] = g[dev_col].rolling('30d').apply(
                    lambda x: len(np.unique(x)), raw=False
                ).fillna(1).astype(int)
                unique_dev_list.append(g.reset_index())
            df = pd.concat(unique_dev_list, ignore_index=True)
        else:
            df['new_device'] = False
            df['device_frequency'] = 1
            df['device_switch_flag'] = False
            df['unique_devices_last_30_days'] = 1

        return df

    def _compute_channel_features(
        self, 
        df: pd.DataFrame, 
        profiles: Optional[Dict[str, BehaviourProfile]]
    ) -> pd.DataFrame:
        logger.debug("Computing channel features...")
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in df.columns else 'customer_id'
        chan_col = TxnCols.CHANNEL if TxnCols.CHANNEL in df.columns else 'channel'

        pref_channel_map = {}
        if profiles:
            for cid, p in profiles.items():
                if hasattr(p, 'statistics'):
                    pref_channel_map[cid] = p.statistics.most_common_channel

        if chan_col in df.columns:
            cum_chan_count = df.groupby([cust_col, chan_col]).cumcount()
            df['new_channel'] = (cum_chan_count == 0).astype(bool)
            df['channel_frequency'] = (cum_chan_count + 1).astype(int)
            
            # Map preferred channel or fallback to most common in df
            cust_mode_chan = df.groupby(cust_col)[chan_col].transform(lambda x: pd.Series.mode(x).iloc[0] if not x.empty else 'UNKNOWN')
            df['preferred_channel'] = df[cust_col].astype(str).map(pref_channel_map).fillna(cust_mode_chan).astype(str)
            df['outside_preferred_channel'] = (df[chan_col] != df['preferred_channel']).astype(bool)
        else:
            df['new_channel'] = False
            df['channel_frequency'] = 1
            df['preferred_channel'] = 'UNKNOWN'
            df['outside_preferred_channel'] = False

        return df

    def _compute_geographic_features(
        self, 
        df: pd.DataFrame, 
        profiles: Optional[Dict[str, BehaviourProfile]]
    ) -> pd.DataFrame:
        logger.debug("Computing geographic features...")
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in df.columns else 'customer_id'
        country_col = TxnCols.COUNTERPARTY_COUNTRY if TxnCols.COUNTERPARTY_COUNTRY in df.columns else 'counterparty_country'

        if country_col in df.columns:
            cum_cntry_count = df.groupby([cust_col, country_col]).cumcount()
            df['new_country'] = (cum_cntry_count == 0).astype(bool)
            df['country_frequency'] = (cum_cntry_count + 1).astype(int)

            # Geographic change
            prev_country = df.groupby(cust_col)[country_col].shift(1)
            df['geographic_change'] = (df[country_col] != prev_country) & prev_country.notna()

            # Cross-border & High-risk country flag
            home_country = df['location_country'] if 'location_country' in df.columns else 'US'
            df['cross_border_transaction'] = (df[country_col] != home_country).astype(bool)

            if ComputedCols.FATF_STATUS in df.columns:
                df['high_risk_country_flag'] = (df[ComputedCols.FATF_STATUS] != 'NORMAL').astype(bool)
            else:
                high_risk_set = {'IR', 'KP', 'MM', 'SY', 'YE'} # Common FATF high risk list
                df['high_risk_country_flag'] = df[country_col].isin(high_risk_set).astype(bool)

            df['distance_from_previous_country'] = df['geographic_change'].astype(float) * 500.0 # Standard approx distance step
        else:
            df['new_country'] = False
            df['country_frequency'] = 1
            df['cross_border_transaction'] = False
            df['high_risk_country_flag'] = False
            df['geographic_change'] = False
            df['distance_from_previous_country'] = 0.0

        return df

    def _compute_historical_features(
        self, 
        df: pd.DataFrame, 
        profiles: Optional[Dict[str, BehaviourProfile]]
    ) -> pd.DataFrame:
        logger.debug("Computing historical customer features...")
        cust_col = TxnCols.CUSTOMER_ID if TxnCols.CUSTOMER_ID in df.columns else 'customer_id'

        # Map metadata fields if present, else fallback
        df['account_age_days'] = df['account_age_days'].astype(int) if 'account_age_days' in df.columns else 0
        df['customer_age_group'] = df['customer_age_group'].astype(str) if 'customer_age_group' in df.columns else 'Unknown'
        df['kyc_level'] = df[CustomerCols.KYC_LEVEL].astype(str) if CustomerCols.KYC_LEVEL in df.columns else 'VERIFIED'
        df['pep_flag'] = df[ComputedCols.IS_PEP].astype(bool) if ComputedCols.IS_PEP in df.columns else False
        df['previous_sar_count'] = df['previous_sar_count'].astype(int) if 'previous_sar_count' in df.columns else 0
        df['historical_average_amount'] = df['customer_average_amount'].astype(float)

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

                # 1. Amount Features
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

                # 2. Velocity Features
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

                # 3. Behaviour Deviation Features
                outside_business_hours=bool(row.get('outside_business_hours', False)),
                outside_preferred_hour=bool(row.get('outside_preferred_hour', False)),
                unusual_weekday=bool(row.get('unusual_weekday', False)),
                unusual_month=bool(row.get('unusual_month', False)),
                amount_deviation_score=float(row.get('amount_deviation_score', 0.0)),
                frequency_deviation_score=float(row.get('frequency_deviation_score', 0.0)),
                behaviour_deviation_score=float(row.get('behaviour_deviation_score', 0.0)),

                # 4. Relationship Features
                new_beneficiary=bool(row.get('new_beneficiary', False)),
                beneficiary_frequency=int(row.get('beneficiary_frequency', 1)),
                beneficiary_amount_average=float(row.get('beneficiary_amount_average', 0.0)),
                beneficiary_amount_std=float(row.get('beneficiary_amount_std', 0.0)),
                beneficiary_transaction_count=int(row.get('beneficiary_transaction_count', 1)),
                beneficiary_is_high_frequency=bool(row.get('beneficiary_is_high_frequency', False)),

                # 5. Device Features
                new_device=bool(row.get('new_device', False)),
                device_frequency=int(row.get('device_frequency', 1)),
                device_switch_flag=bool(row.get('device_switch_flag', False)),
                unique_devices_last_30_days=int(row.get('unique_devices_last_30_days', 1)),

                # 6. Channel Features
                new_channel=bool(row.get('new_channel', False)),
                channel_frequency=int(row.get('channel_frequency', 1)),
                preferred_channel=str(row.get('preferred_channel', 'UNKNOWN')),
                outside_preferred_channel=bool(row.get('outside_preferred_channel', False)),

                # 7. Geographic Features
                new_country=bool(row.get('new_country', False)),
                country_frequency=int(row.get('country_frequency', 1)),
                cross_border_transaction=bool(row.get('cross_border_transaction', False)),
                high_risk_country_flag=bool(row.get('high_risk_country_flag', False)),
                geographic_change=bool(row.get('geographic_change', False)),
                distance_from_previous_country=float(row.get('distance_from_previous_country', 0.0)),

                # 8. Historical Customer Features
                account_age_days=int(row.get('account_age_days', 0)),
                customer_age_group=str(row.get('customer_age_group', 'Unknown')),
                kyc_level=str(row.get('kyc_level', 'VERIFIED')),
                pep_flag=bool(row.get('pep_flag', False)),
                previous_sar_count=int(row.get('previous_sar_count', 0)),
                historical_average_amount=float(row.get('historical_average_amount', 0.0))
            )
            vectors.append(vector)
        return vectors

