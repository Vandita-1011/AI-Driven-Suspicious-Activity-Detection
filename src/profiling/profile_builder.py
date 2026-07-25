import pandas as pd
import numpy as np

from src.constants.column_names import TxnCols, CustomerCols, ComputedCols
from src.profiling.profile_models import CustomerMetadata, BehaviourStatistics, BehaviourFlags, BehaviourProfile
from src.utils.logger import get_logger
from src.exceptions.engine_exceptions import PreprocessingError

logger = get_logger(__name__)

class ProfileBuilder:
    """
    Builds behaviour profiles using vectorized operations for efficiency.
    """
    
    def build_profiles(self, enriched_df: pd.DataFrame) -> dict[str, BehaviourProfile]:
        """
        Computes all customer profiles simultaneously using groupby aggregations.
        """
        if enriched_df.empty:
            return {}
            
        logger.info("Computing vectorized aggregations for customer profiling...")
        
        # 1. Base aggregations per customer
        agg_funcs = {
            TxnCols.AMOUNT: ['mean', 'median', 'max', 'min', 'std', 'count'],
            ComputedCols.HOUR_OF_DAY: lambda x: pd.Series.mode(x).iloc[0] if not x.empty else 0,
            ComputedCols.DAY_OF_WEEK: lambda x: pd.Series.mode(x).iloc[0] if not x.empty else 0,
            'transaction_month': lambda x: pd.Series.mode(x).iloc[0] if not x.empty else 0,
            'is_business_hours': 'mean',
            ComputedCols.IS_WEEKEND: 'mean',
            TxnCols.TRANSACTION_TYPE: lambda x: pd.Series.mode(x).iloc[0] if not x.empty else 'UNKNOWN',
            TxnCols.CHANNEL: lambda x: pd.Series.mode(x).iloc[0] if not x.empty else 'UNKNOWN',
            TxnCols.COUNTERPARTY_ACCOUNT_ID: ['nunique', lambda x: pd.Series.mode(x).iloc[0] if not x.empty else 'UNKNOWN'],
            TxnCols.ACCOUNT_ID: 'nunique',
            TxnCols.COUNTERPARTY_COUNTRY: 'nunique',
            TxnCols.DEVICE_ID: 'nunique',
            'transaction_date': ['nunique', 'min', 'max']
        }
        
        # To avoid KeyError, only aggregate columns that exist
        safe_agg = {}
        for col, funcs in agg_funcs.items():
            if col in enriched_df.columns:
                safe_agg[col] = funcs
                
        grouped = enriched_df.groupby(TxnCols.CUSTOMER_ID)
        stats_df = grouped.agg(safe_agg)
        
        # Flatten multi-index columns
        stats_df.columns = ['_'.join(col).strip() for col in stats_df.columns.values]
        
        # 2. Compute Type Ratios
        if TxnCols.TRANSACTION_TYPE in enriched_df.columns:
            type_counts = enriched_df.pivot_table(
                index=TxnCols.CUSTOMER_ID, 
                columns=TxnCols.TRANSACTION_TYPE, 
                aggfunc='size', fill_value=0
            )
            type_ratios = type_counts.div(type_counts.sum(axis=1), axis=0)
        else:
            type_ratios = pd.DataFrame(index=stats_df.index)
            
        # 3. Retrieve Metadata (take the first instance for each customer)
        meta_cols = [
            'account_age_days', 'customer_age_group', CustomerCols.KYC_LEVEL, 
            ComputedCols.IS_PEP, 'is_high_risk_country_history'
        ]
        meta_cols = [c for c in meta_cols if c in enriched_df.columns]
        meta_df = grouped[meta_cols].first() if meta_cols else pd.DataFrame(index=stats_df.index)

        # Build objects
        profiles = {}
        for cust_id in stats_df.index:
            row = stats_df.loc[cust_id]
            meta_row = meta_df.loc[cust_id] if not meta_df.empty else pd.Series(dtype=float)
            ratio_row = type_ratios.loc[cust_id] if not type_ratios.empty else pd.Series(dtype=float)
            
            profiles[str(cust_id)] = self._construct_profile(str(cust_id), row, meta_row, ratio_row)
            
        return profiles

    def _construct_profile(self, cust_id: str, row: pd.Series, meta_row: pd.Series, ratio_row: pd.Series) -> BehaviourProfile:
        # Extract metadata
        metadata = CustomerMetadata(
            customer_id=cust_id,
            account_age_days=int(meta_row.get('account_age_days', 0)),
            customer_age_group=str(meta_row.get('customer_age_group', 'Unknown')),
            kyc_level=str(meta_row.get(CustomerCols.KYC_LEVEL, 'Unknown')),
            pep_status=bool(meta_row.get(ComputedCols.IS_PEP, False)),
            high_risk_country_history=bool(meta_row.get('is_high_risk_country_history', False)),
            previous_sar_count=0
        )
        
        # Calculate derived frequencies
        total_txns = row.get(f'{TxnCols.AMOUNT}_count', 1)
        unique_days = row.get('transaction_date_nunique', 1)
        # Avoid division by zero
        unique_days = max(1, unique_days)
        unique_weeks = max(1, unique_days / 7)
        unique_months = max(1, unique_days / 30)
        
        # Calculate average transaction gap (days between consecutive transactions)
        date_min = row.get('transaction_date_min')
        date_max = row.get('transaction_date_max')
        if pd.notna(date_min) and pd.notna(date_max) and total_txns > 1:
            try:
                span_days = (pd.to_datetime(date_max) - pd.to_datetime(date_min)).days
                avg_txn_gap_days = float(span_days / max(1, total_txns - 1))
            except Exception:
                avg_txn_gap_days = 0.0
        else:
            avg_txn_gap_days = 0.0

        # Ratios mapping (safe get)
        def _get_ratio(txn_type: str) -> float:
            return float(ratio_row.get(txn_type, 0.0))

        stats = BehaviourStatistics(
            avg_amount=float(row.get(f'{TxnCols.AMOUNT}_mean', 0.0)),
            median_amount=float(row.get(f'{TxnCols.AMOUNT}_median', 0.0)),
            max_amount=float(row.get(f'{TxnCols.AMOUNT}_max', 0.0)),
            min_amount=float(row.get(f'{TxnCols.AMOUNT}_min', 0.0)),
            std_amount=float(row.get(f'{TxnCols.AMOUNT}_std', 0.0) if not pd.isna(row.get(f'{TxnCols.AMOUNT}_std')) else 0.0),
            
            avg_daily_txns=float(total_txns / unique_days),
            avg_weekly_txns=float(total_txns / unique_weeks),
            avg_monthly_txns=float(total_txns / unique_months),
            avg_txn_gap_days=avg_txn_gap_days,
            
            preferred_hour=int(row.get(f'{ComputedCols.HOUR_OF_DAY}_<lambda>', 0)),
            most_active_weekday=int(row.get(f'{ComputedCols.DAY_OF_WEEK}_<lambda>', 0)),
            most_active_month=int(row.get('transaction_month_<lambda>', 0)),
            business_hours_ratio=float(row.get('is_business_hours_mean', 0.0)),
            weekend_ratio=float(row.get(f'{ComputedCols.IS_WEEKEND}_mean', 0.0)),
            
            cash_withdrawal_ratio=_get_ratio('CASH_WITHDRAWAL'),
            deposit_ratio=_get_ratio('DEPOSIT') + _get_ratio('CASH_DEPOSIT'),
            transfer_ratio=_get_ratio('TRANSFER') + _get_ratio('WIRE_TRANSFER'),
            
            unique_beneficiaries=int(row.get(f'{TxnCols.COUNTERPARTY_ACCOUNT_ID}_nunique', 0)),
            unique_accounts=int(row.get(f'{TxnCols.ACCOUNT_ID}_nunique', 0)),
            unique_countries=int(row.get(f'{TxnCols.COUNTERPARTY_COUNTRY}_nunique', 0)),
            unique_devices=int(row.get(f'{TxnCols.DEVICE_ID}_nunique', 0)),
            unique_channels=int(row.get(f'{TxnCols.CHANNEL}_<lambda>', 1)), # Fallback approx
            
            most_common_beneficiary=str(row.get(f'{TxnCols.COUNTERPARTY_ACCOUNT_ID}_<lambda>', 'UNKNOWN')),
            most_common_channel=str(row.get(f'{TxnCols.CHANNEL}_<lambda>', 'UNKNOWN')),
            most_common_txn_type=str(row.get(f'{TxnCols.TRANSACTION_TYPE}_<lambda>', 'UNKNOWN'))
        )
        
        flags = self._compute_flags(stats)
        confidence = self._compute_confidence(total_txns, metadata.account_age_days, stats)
        summary = self._generate_summary(stats, flags)
        
        return BehaviourProfile(
            customer_id=cust_id,
            metadata=metadata,
            statistics=stats,
            flags=flags,
            confidence_score=confidence,
            summary=summary
        )

    def _compute_flags(self, stats: BehaviourStatistics) -> BehaviourFlags:
        return BehaviourFlags(
            salary_account=stats.deposit_ratio > 0.8 and stats.avg_monthly_txns < 5,
            business_account=stats.unique_beneficiaries > 20 and stats.avg_monthly_txns > 50,
            frequent_transfer_user=stats.transfer_ratio > 0.6 and stats.avg_weekly_txns > 5,
            cash_intensive_customer=(stats.cash_withdrawal_ratio + stats.deposit_ratio) > 0.5,
            dormant_customer=stats.avg_monthly_txns < 0.5,
            high_activity_customer=stats.avg_daily_txns > 3,
            night_activity_customer=stats.business_hours_ratio < 0.2,
            weekend_heavy_customer=stats.weekend_ratio > 0.4,
            international_customer=stats.unique_countries > 1,
            digital_first_customer=stats.most_common_channel in ['MOBILE', 'WEB']
        )

    def _compute_confidence(self, total_txns: float, account_age: int, stats: BehaviourStatistics) -> float:
        # 1. Transaction history length confidence (up to 50 txns)
        txn_conf = min(total_txns / 50.0, 1.0)
        
        # 2. Account age confidence (up to 180 days)
        age_conf = min(account_age / 180.0, 1.0) if account_age > 0 else 0.1
        
        # 3. Behavioural consistency (lower coefficient of variation CV = std/mean -> higher consistency)
        if stats.avg_amount > 0:
            cv = stats.std_amount / stats.avg_amount
            consistency_conf = max(0.0, min(1.0, 1.0 - (cv / 3.0)))
        else:
            consistency_conf = 0.5

        # Weighted combination: 50% history length, 30% account age, 20% consistency
        conf = (txn_conf * 0.50) + (age_conf * 0.30) + (consistency_conf * 0.20)
        return float(round(max(0.0, min(1.0, conf)), 2))

    def _generate_summary(self, stats: BehaviourStatistics, flags: BehaviourFlags) -> str:
        # Deterministic generation
        freq = "rarely" if flags.dormant_customer else f"{int(stats.avg_weekly_txns)} times a week"
        hour_period = "night" if flags.night_activity_customer else "business hours"
        
        summary = (
            f"Customer transacts {freq}, typically during {hour_period}. "
            f"Average transaction amount is roughly {stats.avg_amount:,.2f}. "
        )
        if flags.international_customer:
            summary += "Customer frequently transacts internationally. "
        else:
            summary += "Customer operates domestically. "
            
        if flags.cash_intensive_customer:
            summary += "Profile is highly cash intensive."
            
        return summary
