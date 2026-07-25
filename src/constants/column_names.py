"""
Column Name Constants
=====================
Every CSV column name as a typed string constant, organised per table.

Rules:
  - Never use raw string literals like ``"transaction_id"`` in module code.
  - Always import the constant class and reference it (e.g. ``TxnCols.AMOUNT``).
  - Column names here match EXACTLY what the generator writes to CSV.

Tables covered (12 CSVs):
    TxnCols                  transaction.csv
    CustomerCols             customer.csv
    AccountCols              account.csv
    DeviceCols               device.csv
    BeneficiaryCols          beneficiary.csv
    MerchantCols             merchant.csv
    LocationCols             location.csv
    BranchCols               branch.csv
    CountryRiskCols          country_risk.csv
    RelationshipCols         customer_relationship.csv
    FraudRingCols            fraud_ring.csv
    FraudRingMembershipCols  customer_fraud_ring_membership.csv
    ComputedCols             AI-engine generated columns (enrichment + features)
"""


class TxnCols:
    """Column constants for ``transaction.csv`` (17 columns)."""

    TRANSACTION_ID = "transaction_id"
    ACCOUNT_ID = "account_id"
    CUSTOMER_ID = "customer_id"
    TIMESTAMP = "timestamp"
    TRANSACTION_TYPE = "transaction_type"
    CHANNEL = "channel"
    AMOUNT = "amount"
    CURRENCY = "currency"
    COUNTERPARTY_ACCOUNT_ID = "counterparty_account_id"
    COUNTERPARTY_NAME = "counterparty_name"
    COUNTERPARTY_COUNTRY = "counterparty_country"
    MERCHANT_ID = "merchant_id"
    DEVICE_ID = "device_id"
    LOCATION_ID = "location_id"
    BALANCE_AFTER = "balance_after"
    FLAG_LABEL = "flag_label"
    AML_SCENARIO_TAG = "aml_scenario_tag"

    # Full ordered list — used for schema validation
    ALL: list[str] = [
        TRANSACTION_ID, ACCOUNT_ID, CUSTOMER_ID, TIMESTAMP, TRANSACTION_TYPE,
        CHANNEL, AMOUNT, CURRENCY, COUNTERPARTY_ACCOUNT_ID, COUNTERPARTY_NAME,
        COUNTERPARTY_COUNTRY, MERCHANT_ID, DEVICE_ID, LOCATION_ID,
        BALANCE_AFTER, FLAG_LABEL, AML_SCENARIO_TAG,
    ]


class CustomerCols:
    """Column constants for ``customer.csv`` (17 columns)."""

    CUSTOMER_ID = "customer_id"
    FULL_NAME = "full_name"
    DOB = "dob"
    AGE = "age"
    GENDER = "gender"
    NATIONALITY = "nationality"
    OCCUPATION = "occupation"
    PROFILE_SEGMENT = "profile_segment"
    ANNUAL_INCOME = "annual_income"
    INCOME_BAND = "income_band"
    KYC_LEVEL = "kyc_level"
    IS_PEP = "is_pep"
    SANCTIONS_HIT = "sanctions_hit"
    BENEFICIAL_OWNER_ID = "beneficial_owner_id"
    ONBOARDING_DATE = "onboarding_date"
    BRANCH_ID = "branch_id"
    RISK_SCORE = "risk_score"

    ALL: list[str] = [
        CUSTOMER_ID, FULL_NAME, DOB, AGE, GENDER, NATIONALITY, OCCUPATION,
        PROFILE_SEGMENT, ANNUAL_INCOME, INCOME_BAND, KYC_LEVEL, IS_PEP,
        SANCTIONS_HIT, BENEFICIAL_OWNER_ID, ONBOARDING_DATE, BRANCH_ID, RISK_SCORE,
    ]


class AccountCols:
    """Column constants for ``account.csv`` (10 columns)."""

    ACCOUNT_ID = "account_id"
    CUSTOMER_ID = "customer_id"
    ACCOUNT_TYPE = "account_type"
    BRANCH_ID = "branch_id"
    OPEN_DATE = "open_date"
    CURRENCY = "currency"
    STATUS = "status"
    CURRENT_BALANCE = "current_balance"
    AVG_MONTHLY_BALANCE = "avg_monthly_balance"
    LINKED_ACCOUNTS = "linked_accounts"

    ALL: list[str] = [
        ACCOUNT_ID, CUSTOMER_ID, ACCOUNT_TYPE, BRANCH_ID, OPEN_DATE,
        CURRENCY, STATUS, CURRENT_BALANCE, AVG_MONTHLY_BALANCE, LINKED_ACCOUNTS,
    ]


class DeviceCols:
    """Column constants for ``device.csv`` (6 columns)."""

    DEVICE_ID = "device_id"
    CUSTOMER_ID = "customer_id"
    DEVICE_TYPE = "device_type"
    OS = "os"
    FIRST_SEEN_DATE = "first_seen_date"
    IS_SHARED_DEVICE = "is_shared_device"

    ALL: list[str] = [
        DEVICE_ID, CUSTOMER_ID, DEVICE_TYPE, OS, FIRST_SEEN_DATE, IS_SHARED_DEVICE,
    ]


class BeneficiaryCols:
    """Column constants for ``beneficiary.csv`` (6 columns)."""

    BENEFICIARY_ID = "beneficiary_id"
    CUSTOMER_ID = "customer_id"
    BENEFICIARY_NAME = "beneficiary_name"
    RELATIONSHIP_TYPE = "relationship_type"
    COUNTRY_CODE = "country_code"
    ADDED_DATE = "added_date"

    ALL: list[str] = [
        BENEFICIARY_ID, CUSTOMER_ID, BENEFICIARY_NAME,
        RELATIONSHIP_TYPE, COUNTRY_CODE, ADDED_DATE,
    ]


class MerchantCols:
    """Column constants for ``merchant.csv`` (6 columns)."""

    MERCHANT_ID = "merchant_id"
    MERCHANT_NAME = "merchant_name"
    MCC_CODE = "mcc_code"
    CATEGORY = "category"
    COUNTRY_CODE = "country_code"
    RISK_LEVEL = "risk_level"

    ALL: list[str] = [
        MERCHANT_ID, MERCHANT_NAME, MCC_CODE, CATEGORY, COUNTRY_CODE, RISK_LEVEL,
    ]


class LocationCols:
    """Column constants for ``location.csv`` (6 columns)."""

    LOCATION_ID = "location_id"
    CITY = "city"
    COUNTRY_CODE = "country_code"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    IS_HIGH_RISK = "is_high_risk"

    ALL: list[str] = [
        LOCATION_ID, CITY, COUNTRY_CODE, LATITUDE, LONGITUDE, IS_HIGH_RISK,
    ]


class BranchCols:
    """Column constants for ``branch.csv`` (5 columns)."""

    BRANCH_ID = "branch_id"
    BRANCH_NAME = "branch_name"
    COUNTRY_CODE = "country_code"
    CITY = "city"
    IS_HIGH_RISK_BRANCH = "is_high_risk_branch"

    ALL: list[str] = [
        BRANCH_ID, BRANCH_NAME, COUNTRY_CODE, CITY, IS_HIGH_RISK_BRANCH,
    ]


class CountryRiskCols:
    """Column constants for ``country_risk.csv`` (4 columns)."""

    COUNTRY_CODE = "country_code"
    COUNTRY_NAME = "country_name"
    FATF_STATUS = "fatf_status"
    RISK_SCORE = "risk_score"

    ALL: list[str] = [COUNTRY_CODE, COUNTRY_NAME, FATF_STATUS, RISK_SCORE]


class RelationshipCols:
    """Column constants for ``customer_relationship.csv`` (5 columns)."""

    RELATIONSHIP_ID = "relationship_id"
    CUSTOMER_ID_1 = "customer_id_1"
    CUSTOMER_ID_2 = "customer_id_2"
    RELATIONSHIP_TYPE = "relationship_type"
    IS_SYMMETRIC = "is_symmetric"

    ALL: list[str] = [
        RELATIONSHIP_ID, CUSTOMER_ID_1, CUSTOMER_ID_2,
        RELATIONSHIP_TYPE, IS_SYMMETRIC,
    ]


class FraudRingCols:
    """Column constants for ``fraud_ring.csv`` (5 columns)."""

    FRAUD_RING_ID = "fraud_ring_id"
    RING_NAME = "ring_name"
    RING_TYPE = "ring_type"
    FORMATION_DATE = "formation_date"
    NUM_MEMBERS = "num_members"

    ALL: list[str] = [
        FRAUD_RING_ID, RING_NAME, RING_TYPE, FORMATION_DATE, NUM_MEMBERS,
    ]


class FraudRingMembershipCols:
    """Column constants for ``customer_fraud_ring_membership.csv`` (4 columns)."""

    MEMBERSHIP_ID = "membership_id"
    FRAUD_RING_ID = "fraud_ring_id"
    CUSTOMER_ID = "customer_id"
    ROLE = "role"

    ALL: list[str] = [MEMBERSHIP_ID, FRAUD_RING_ID, CUSTOMER_ID, ROLE]


class ComputedCols:
    """
    Column names added by the AI engine during preprocessing and feature engineering.

    These columns do NOT exist in the raw CSVs — they are derived and appended
    to the enriched DataFrame as the pipeline progresses.
    """

    # ── Enrichment joins (added by DataEnricher) ────────────────────────
    PROFILE_SEGMENT = "profile_segment"
    ANNUAL_INCOME = "annual_income"
    KYC_LEVEL = "kyc_level"
    IS_PEP = "is_pep"
    SANCTIONS_HIT = "sanctions_hit"
    CUSTOMER_RISK_SCORE = "customer_risk_score"
    ACCOUNT_STATUS = "account_status"
    AVG_MONTHLY_BALANCE = "avg_monthly_balance"
    FATF_STATUS = "fatf_status"
    COUNTRY_RISK_SCORE = "country_risk_score"
    MERCHANT_RISK_LEVEL = "merchant_risk_level"
    IS_HIGH_RISK_LOCATION = "is_high_risk_location"
    IS_HIGH_RISK_BRANCH = "is_high_risk_branch"

    # ── Transaction features (added by TransactionFeatureExtractor) ─────
    HOUR_OF_DAY = "hour_of_day"
    DAY_OF_WEEK = "day_of_week"
    IS_WEEKEND = "is_weekend"
    IS_ROUND_AMOUNT = "is_round_amount"
    AMOUNT_TO_INCOME_RATIO = "amount_to_income_ratio"
    AMOUNT_TO_AVG_BALANCE_RATIO = "amount_to_avg_balance_ratio"
    TXN_COUNT_24H = "txn_count_24h"
    TXN_AMOUNT_24H = "txn_amount_24h"
    TXN_COUNT_1H = "txn_count_1h"
    IS_DORMANT_ACCOUNT = "is_dormant_account"
    IS_HIGH_RISK_COUNTERPARTY = "is_high_risk_counterparty"
    IS_INTERNATIONAL = "is_international"
    DAYS_SINCE_ONBOARDING = "days_since_onboarding"

    # ── Customer features (added by CustomerFeatureExtractor) ───────────
    PEP_RISK_FLAG = "pep_risk_flag"
    SANCTIONS_RISK_FLAG = "sanctions_risk_flag"
    KYC_RISK_SCORE = "kyc_risk_score"
    INCOME_RISK_BAND = "income_risk_band"
    SEGMENT_RISK_WEIGHT = "segment_risk_weight"

    # ── Network features (added by NetworkFeatureExtractor) ─────────────
    IN_FRAUD_RING = "in_fraud_ring"
    FRAUD_RING_ROLE = "fraud_ring_role"
    RELATIONSHIP_COUNT = "relationship_count"
    COUNTERPARTY_RELATIONSHIP_EXISTS = "counterparty_relationship_exists"
    SHARED_DEVICE_FLAG = "shared_device_flag"

    # ── Engine output columns (added by engines + fusion) ───────────────
    RULE_SCORE = "rule_score"
    RULE_FLAGS = "rule_flags"
    BEHAVIOUR_SCORE = "behaviour_score"
    BEHAVIOUR_DEVIATIONS = "behaviour_deviations"
    STATISTICAL_SCORE = "statistical_score"
    STATISTICAL_ANOMALIES = "statistical_anomalies"
    ML_SCORE = "ml_score"
    PATTERN_SCORE = "pattern_score"
    MATCHED_PATTERNS = "matched_patterns"
    FUSED_RISK_SCORE = "fused_risk_score"
    RISK_LEVEL = "risk_level"

    # ── Final output columns ─────────────────────────────────────────────
    ALERT_PRIORITY = "alert_priority"
    EXPLANATION = "explanation"
    RECOMMENDED_ACTION = "recommended_action"
