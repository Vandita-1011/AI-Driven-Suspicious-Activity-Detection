"""
Data Enricher
=============
Creates derived metadata required before feature engineering.
Examples: customer_age_group, account_age_days, is_business_hours.
"""
import pandas as pd
import numpy as np
from datetime import datetime

from src.constants.column_names import (
    AccountCols, BranchCols, CountryRiskCols, CustomerCols,
    LocationCols, MerchantCols, TxnCols, ComputedCols
)
from src.data.dataset_context import DatasetContext
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataEnricher:
    """
    Creates derived preprocessing metadata (non-ML features) and joins reference data.
    """
    def __init__(self, context: DatasetContext) -> None:
        self.context = context
        
    def enrich(self, cleaned_txns: pd.DataFrame, cleaned_customers: pd.DataFrame, cleaned_accounts: pd.DataFrame) -> pd.DataFrame:
        """
        Generates metadata and enriches transactions with customer/account data.
        """
        logger.info("Enriching data with derived metadata...")
        
        # 1. Enrich Customers metadata
        customers = self._enrich_customers_metadata(cleaned_customers)
        
        # 2. Enrich Accounts metadata
        accounts = self._enrich_accounts_metadata(cleaned_accounts)
        
        # 3. Enrich Transactions metadata
        txns = self._enrich_transactions_metadata(cleaned_txns)
        
        # 4. Join reference data
        df = self._join_data(txns, customers, accounts)
        
        logger.info("Data enrichment complete. Final shape: %s", df.shape)
        return df

    def _enrich_customers_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        
        if CustomerCols.AGE in df.columns:
            # Create age group
            bins = [0, 18, 30, 50, 70, 120]
            labels = ["Under 18", "18-30", "31-50", "51-70", "Over 70"]
            df['customer_age_group'] = pd.cut(df[CustomerCols.AGE], bins=bins, labels=labels, right=True)
            df['customer_age_group'] = df['customer_age_group'].astype(str).replace('nan', 'Unknown')
            logger.debug("Derived metadata: customer_age_group")
            
        return df

    def _enrich_accounts_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        
        if AccountCols.OPEN_DATE in df.columns:
            # Calculate account age in days relative to current data snapshot date
            # We use a fixed date for the prototype to avoid drifting results if run in the future
            snapshot_date = pd.to_datetime('2024-01-01', utc=True)
            open_dates = pd.to_datetime(df[AccountCols.OPEN_DATE], utc=True, errors='coerce')
            
            df['account_age_days'] = (snapshot_date - open_dates).dt.days
            # Cap at 0 in case of future dates
            df['account_age_days'] = df['account_age_days'].clip(lower=0)
            logger.debug("Derived metadata: account_age_days")
            
        return df

    def _enrich_transactions_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        
        if TxnCols.TIMESTAMP in df.columns:
            ts = pd.to_datetime(df[TxnCols.TIMESTAMP], utc=True, errors='coerce')
            df['transaction_date'] = ts.dt.date
            
            # Note: hour/day/month/is_weekend are generated in TimestampProcessor
            
            # Generate is_business_hours (e.g. 9am to 5pm)
            if ComputedCols.HOUR_OF_DAY in df.columns:
                df['is_business_hours'] = df[ComputedCols.HOUR_OF_DAY].between(9, 17).astype(bool)
                logger.debug("Derived metadata: is_business_hours")
                
        return df

    def _join_data(self, txns: pd.DataFrame, customers: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Joining tables to form flat enriched dataset...")
        df = txns.copy()
        
        if not accounts.empty:
            df = df.merge(
                accounts[[AccountCols.ACCOUNT_ID, AccountCols.STATUS, 'account_age_days', AccountCols.AVG_MONTHLY_BALANCE]],
                on=AccountCols.ACCOUNT_ID,
                how="left"
            )
            df.rename(columns={
                AccountCols.STATUS: ComputedCols.ACCOUNT_STATUS,
                AccountCols.AVG_MONTHLY_BALANCE: ComputedCols.AVG_MONTHLY_BALANCE
            }, inplace=True)
            
        if not customers.empty:
            df = df.merge(
                customers[[
                    CustomerCols.CUSTOMER_ID, CustomerCols.PROFILE_SEGMENT, 
                    'customer_age_group', CustomerCols.ANNUAL_INCOME, 
                    CustomerCols.KYC_LEVEL, CustomerCols.IS_PEP, 
                    CustomerCols.SANCTIONS_HIT, CustomerCols.RISK_SCORE
                ]],
                on=CustomerCols.CUSTOMER_ID,
                how="left"
            )
            df.rename(columns={CustomerCols.RISK_SCORE: ComputedCols.CUSTOMER_RISK_SCORE}, inplace=True)
            
        if not self.context.country_risk.empty and TxnCols.COUNTERPARTY_COUNTRY in df.columns:
            df = df.merge(
                self.context.country_risk[[CountryRiskCols.COUNTRY_CODE, CountryRiskCols.FATF_STATUS, CountryRiskCols.RISK_SCORE]],
                left_on=TxnCols.COUNTERPARTY_COUNTRY,
                right_on=CountryRiskCols.COUNTRY_CODE,
                how="left"
            )
            df.rename(columns={
                CountryRiskCols.FATF_STATUS: ComputedCols.FATF_STATUS,
                CountryRiskCols.RISK_SCORE: ComputedCols.COUNTRY_RISK_SCORE
            }, inplace=True)
            df.drop(columns=[CountryRiskCols.COUNTRY_CODE], inplace=True)
            
        # Ensure booleans
        for col in [ComputedCols.IS_PEP, ComputedCols.SANCTIONS_HIT]:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)
                
        return df
