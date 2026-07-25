"""
Data Enricher
=============
Performs multi-table joins to create a single, enriched transactions DataFrame.
"""
import pandas as pd

from src.constants.column_names import (
    AccountCols, BranchCols, CountryRiskCols, CustomerCols,
    LocationCols, MerchantCols, TxnCols, ComputedCols
)
from src.data.dataset_context import DatasetContext
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataEnricher:
    """
    Joins reference data onto the transactions table.
    """

    def __init__(self, context: DatasetContext) -> None:
        self.context = context

    def enrich(self, cleaned_txns: pd.DataFrame, cleaned_customers: pd.DataFrame) -> pd.DataFrame:
        """
        Enriches transactions with customer, account, and reference data.
        """
        logger.debug("Enriching transactions...")
        df = cleaned_txns.copy()

        # Join Accounts
        if not self.context.accounts.empty:
            df = df.merge(
                self.context.accounts[[AccountCols.ACCOUNT_ID, AccountCols.STATUS, AccountCols.AVG_MONTHLY_BALANCE]],
                on=AccountCols.ACCOUNT_ID,
                how="left"
            )
            df.rename(columns={
                AccountCols.STATUS: ComputedCols.ACCOUNT_STATUS,
                AccountCols.AVG_MONTHLY_BALANCE: ComputedCols.AVG_MONTHLY_BALANCE
            }, inplace=True)

        # Join Customers
        if not cleaned_customers.empty:
            df = df.merge(
                cleaned_customers[[
                    CustomerCols.CUSTOMER_ID, CustomerCols.PROFILE_SEGMENT, 
                    CustomerCols.ANNUAL_INCOME, CustomerCols.KYC_LEVEL, 
                    CustomerCols.IS_PEP, CustomerCols.SANCTIONS_HIT, 
                    CustomerCols.RISK_SCORE
                ]],
                on=CustomerCols.CUSTOMER_ID,
                how="left"
            )
            df.rename(columns={CustomerCols.RISK_SCORE: ComputedCols.CUSTOMER_RISK_SCORE}, inplace=True)

        # Join Country Risk for Counterparty
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

        # Ensure boolean columns are strictly boolean after left joins
        bool_cols = [ComputedCols.IS_PEP, ComputedCols.SANCTIONS_HIT]
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)

        logger.debug("Enrichment complete. Result shape: %s", df.shape)
        return df
