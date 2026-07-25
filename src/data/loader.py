"""
Dataset Loader
==============
Reads CSVs from the dataset directory, performs extensive schema validation,
and constructs the unified DatasetContext.
"""
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

from src.config.settings import get_settings
from src.constants.column_names import (
    AccountCols, BeneficiaryCols, BranchCols, CountryRiskCols, CustomerCols,
    DeviceCols, FraudRingCols, FraudRingMembershipCols, LocationCols,
    MerchantCols, RelationshipCols, TxnCols,
)
from src.data.dataset_context import DatasetContext
from src.interfaces.base_loader import BaseDataLoader
from src.utils.io_helpers import load_csv_safe, resolve_path
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.utils.validators import (
    validate_columns, validate_not_empty, validate_no_duplicates,
    validate_foreign_key, validate_dtypes, validate_no_nulls,
    validate_timestamp, validate_value_range
)

logger = get_logger(__name__)


class DatasetLoader(BaseDataLoader):
    """
    Loads all CSV files and applies comprehensive data quality validations.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.settings = get_settings()
        
        if data_dir is not None:
            self.data_dir = resolve_path(data_dir)
        else:
            self.data_dir = resolve_path(self.settings.dataset.path)
            
        self.file_map = self.settings.dataset.files

    @timed("Dataset Loading and Validation")
    def load(self) -> DatasetContext:
        """
        Loads all required datasets and validates relationships and schemas.
        """
        logger.info("Starting dataset load from: %s", self.data_dir)
        context = DatasetContext()

        # 1. Load DataFrames
        context.transactions = self._load_csv("transactions", "Transactions")
        context.customers = self._load_csv("customers", "Customers")
        context.accounts = self._load_csv("accounts", "Accounts")
        context.devices = self._load_csv("devices", "Devices")
        context.beneficiaries = self._load_csv("beneficiaries", "Beneficiaries")
        context.merchants = self._load_csv("merchants", "Merchants")
        context.locations = self._load_csv("locations", "Locations")
        context.branches = self._load_csv("branches", "Branches")
        context.country_risk = self._load_csv("country_risk", "Country Risk")
        context.relationships = self._load_csv("customer_relationships", "Relationships")
        context.fraud_rings = self._load_csv("fraud_rings", "Fraud Rings")
        context.fraud_ring_memberships = self._load_csv("fraud_ring_memberships", "Fraud Ring Memberships")

        # 2. Basic Structural Validations (Columns & Empty checks)
        self._validate_structure(context)

        # 3. Primary Key & Missing Value Validations
        self._validate_pks_and_nulls(context)

        # 4. Type & Timestamp Validations
        self._validate_types_and_ranges(context)

        # 5. Foreign Key Relationship Validations
        self._validate_foreign_keys(context)

        logger.info("All data loaded and validated successfully.")
        return context

    def _load_csv(self, file_key: str, table_name: str) -> pd.DataFrame:
        """Loads a single CSV file, logging row and column counts."""
        filename = self.file_map[file_key]
        path = self.data_dir / filename
        df = load_csv_safe(path, table_name)
        logger.info("Dataset loaded: %s | Rows: %d | Cols: %d", table_name, len(df), len(df.columns))
        return df

    def _validate_structure(self, ctx: DatasetContext) -> None:
        """Validates that expected columns exist and primary tables are not empty."""
        logger.info("Validating structural schemas...")
        validate_not_empty(ctx.transactions, "Transactions")
        validate_not_empty(ctx.customers, "Customers")
        validate_not_empty(ctx.accounts, "Accounts")

        validate_columns(ctx.transactions, TxnCols.ALL, "Transactions")
        validate_columns(ctx.customers, CustomerCols.ALL, "Customers")
        validate_columns(ctx.accounts, AccountCols.ALL, "Accounts")
        validate_columns(ctx.devices, DeviceCols.ALL, "Devices")
        validate_columns(ctx.beneficiaries, BeneficiaryCols.ALL, "Beneficiaries")
        validate_columns(ctx.merchants, MerchantCols.ALL, "Merchants")
        validate_columns(ctx.locations, LocationCols.ALL, "Locations")
        validate_columns(ctx.branches, BranchCols.ALL, "Branches")
        validate_columns(ctx.country_risk, CountryRiskCols.ALL, "Country Risk")
        validate_columns(ctx.relationships, RelationshipCols.ALL, "Relationships")
        validate_columns(ctx.fraud_rings, FraudRingCols.ALL, "Fraud Rings")
        validate_columns(ctx.fraud_ring_memberships, FraudRingMembershipCols.ALL, "Fraud Ring Memberships")
        logger.info("Structural validation completed.")

    def _validate_pks_and_nulls(self, ctx: DatasetContext) -> None:
        """Validates primary keys (uniqueness) and required non-null fields."""
        logger.info("Validating primary keys and missing values...")
        
        # Transactions
        validate_no_duplicates(ctx.transactions, TxnCols.TRANSACTION_ID, "Transactions")
        validate_no_nulls(ctx.transactions, [TxnCols.TRANSACTION_ID, TxnCols.ACCOUNT_ID, TxnCols.CUSTOMER_ID, TxnCols.AMOUNT], "Transactions")
        
        # Customers
        validate_no_duplicates(ctx.customers, CustomerCols.CUSTOMER_ID, "Customers")
        validate_no_nulls(ctx.customers, [CustomerCols.CUSTOMER_ID, CustomerCols.FULL_NAME, CustomerCols.DOB], "Customers")
        
        # Accounts
        validate_no_duplicates(ctx.accounts, AccountCols.ACCOUNT_ID, "Accounts")
        validate_no_nulls(ctx.accounts, [AccountCols.ACCOUNT_ID, AccountCols.CUSTOMER_ID, AccountCols.BRANCH_ID], "Accounts")

        # Reference tables PKs
        validate_no_duplicates(ctx.devices, DeviceCols.DEVICE_ID, "Devices")
        validate_no_duplicates(ctx.beneficiaries, BeneficiaryCols.BENEFICIARY_ID, "Beneficiaries")
        validate_no_duplicates(ctx.merchants, MerchantCols.MERCHANT_ID, "Merchants")
        validate_no_duplicates(ctx.locations, LocationCols.LOCATION_ID, "Locations")
        validate_no_duplicates(ctx.branches, BranchCols.BRANCH_ID, "Branches")
        validate_no_duplicates(ctx.country_risk, CountryRiskCols.COUNTRY_CODE, "Country Risk")
        validate_no_duplicates(ctx.relationships, RelationshipCols.RELATIONSHIP_ID, "Relationships")
        validate_no_duplicates(ctx.fraud_rings, FraudRingCols.FRAUD_RING_ID, "Fraud Rings")
        validate_no_duplicates(ctx.fraud_ring_memberships, FraudRingMembershipCols.MEMBERSHIP_ID, "Fraud Ring Memberships")
        
        logger.info("Primary key and null validations completed.")

    def _validate_types_and_ranges(self, ctx: DatasetContext) -> None:
        """Validates specific data types, timestamps, and numeric ranges."""
        logger.info("Validating data types and timestamps...")
        
        # Timestamps
        validate_timestamp(ctx.transactions, TxnCols.TIMESTAMP, "Transactions")
        validate_timestamp(ctx.customers, CustomerCols.DOB, "Customers")
        validate_timestamp(ctx.customers, CustomerCols.ONBOARDING_DATE, "Customers")
        validate_timestamp(ctx.accounts, AccountCols.OPEN_DATE, "Accounts")

        # Numeric constraints
        validate_value_range(ctx.transactions, TxnCols.AMOUNT, min_val=0.01, table_name="Transactions")
        validate_value_range(ctx.customers, CustomerCols.AGE, min_val=0.0, table_name="Customers")
        
        # Type coercions via warnings (will be coerced in Preprocessor later, but loader checks them)
        expected_txn_types = {TxnCols.AMOUNT: 'float64', TxnCols.BALANCE_AFTER: 'float64'}
        validate_dtypes(ctx.transactions, expected_txn_types, "Transactions")
        
        logger.info("Type and range validation completed.")

    def _validate_foreign_keys(self, ctx: DatasetContext) -> None:
        """Validates referential integrity across the datasets."""
        logger.info("Validating foreign key relationships...")
        
        # Transactions -> Accounts & Customers & Merchants & Devices & Locations
        validate_foreign_key(ctx.transactions, TxnCols.ACCOUNT_ID, ctx.accounts, AccountCols.ACCOUNT_ID, "Transactions", "Accounts", allow_nulls=False)
        validate_foreign_key(ctx.transactions, TxnCols.CUSTOMER_ID, ctx.customers, CustomerCols.CUSTOMER_ID, "Transactions", "Customers", allow_nulls=False)
        validate_foreign_key(ctx.transactions, TxnCols.MERCHANT_ID, ctx.merchants, MerchantCols.MERCHANT_ID, "Transactions", "Merchants", allow_nulls=True)
        validate_foreign_key(ctx.transactions, TxnCols.DEVICE_ID, ctx.devices, DeviceCols.DEVICE_ID, "Transactions", "Devices", allow_nulls=True)
        validate_foreign_key(ctx.transactions, TxnCols.LOCATION_ID, ctx.locations, LocationCols.LOCATION_ID, "Transactions", "Locations", allow_nulls=True)
        validate_foreign_key(ctx.transactions, TxnCols.COUNTERPARTY_COUNTRY, ctx.country_risk, CountryRiskCols.COUNTRY_CODE, "Transactions", "Country Risk", allow_nulls=True)

        # Accounts -> Branches
        validate_foreign_key(ctx.accounts, AccountCols.BRANCH_ID, ctx.branches, BranchCols.BRANCH_ID, "Accounts", "Branches", allow_nulls=False)

        # Customers -> Branches & Customers (Beneficial Owner)
        validate_foreign_key(ctx.customers, CustomerCols.BRANCH_ID, ctx.branches, BranchCols.BRANCH_ID, "Customers", "Branches", allow_nulls=False)
        validate_foreign_key(ctx.customers, CustomerCols.BENEFICIAL_OWNER_ID, ctx.customers, CustomerCols.CUSTOMER_ID, "Customers", "Customers", allow_nulls=True)

        # Devices -> Customers
        validate_foreign_key(ctx.devices, DeviceCols.CUSTOMER_ID, ctx.customers, CustomerCols.CUSTOMER_ID, "Devices", "Customers", allow_nulls=False)

        # Beneficiaries -> Customers & Country Risk
        validate_foreign_key(ctx.beneficiaries, BeneficiaryCols.CUSTOMER_ID, ctx.customers, CustomerCols.CUSTOMER_ID, "Beneficiaries", "Customers", allow_nulls=False)
        validate_foreign_key(ctx.beneficiaries, BeneficiaryCols.COUNTRY_CODE, ctx.country_risk, CountryRiskCols.COUNTRY_CODE, "Beneficiaries", "Country Risk", allow_nulls=True)

        # Branches & Locations & Merchants -> Country Risk
        validate_foreign_key(ctx.branches, BranchCols.COUNTRY_CODE, ctx.country_risk, CountryRiskCols.COUNTRY_CODE, "Branches", "Country Risk", allow_nulls=True)
        validate_foreign_key(ctx.locations, LocationCols.COUNTRY_CODE, ctx.country_risk, CountryRiskCols.COUNTRY_CODE, "Locations", "Country Risk", allow_nulls=True)
        validate_foreign_key(ctx.merchants, MerchantCols.COUNTRY_CODE, ctx.country_risk, CountryRiskCols.COUNTRY_CODE, "Merchants", "Country Risk", allow_nulls=True)

        # Relationships -> Customers
        validate_foreign_key(ctx.relationships, RelationshipCols.CUSTOMER_ID_1, ctx.customers, CustomerCols.CUSTOMER_ID, "Relationships", "Customers", allow_nulls=False)
        validate_foreign_key(ctx.relationships, RelationshipCols.CUSTOMER_ID_2, ctx.customers, CustomerCols.CUSTOMER_ID, "Relationships", "Customers", allow_nulls=False)

        # Fraud Rings Memberships -> Customers & Fraud Rings
        validate_foreign_key(ctx.fraud_ring_memberships, FraudRingMembershipCols.CUSTOMER_ID, ctx.customers, CustomerCols.CUSTOMER_ID, "Fraud Ring Memberships", "Customers", allow_nulls=False)
        validate_foreign_key(ctx.fraud_ring_memberships, FraudRingMembershipCols.FRAUD_RING_ID, ctx.fraud_rings, FraudRingCols.FRAUD_RING_ID, "Fraud Ring Memberships", "Fraud Rings", allow_nulls=False)

        logger.info("Foreign key validation completed.")

