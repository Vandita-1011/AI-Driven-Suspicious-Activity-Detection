"""
Data Schemas
============
Provides typed dictionaries mapping table names to their expected columns.
Used purely for documentation and reference; actual validation uses
the constants defined in `src/constants/column_names.py`.
"""
from typing import TypedDict

class TransactionSchema(TypedDict):
    transaction_id: str
    account_id: str
    customer_id: str
    timestamp: str
    transaction_type: str
    channel: str
    amount: float
    currency: str
    counterparty_account_id: str
    counterparty_name: str
    counterparty_country: str
    merchant_id: str
    device_id: str
    location_id: str
    balance_after: float
    flag_label: str
    aml_scenario_tag: str

class CustomerSchema(TypedDict):
    customer_id: str
    full_name: str
    dob: str
    age: int
    gender: str
    nationality: str
    occupation: str
    profile_segment: str
    annual_income: float
    income_band: str
    kyc_level: str
    is_pep: bool
    sanctions_hit: bool
    beneficial_owner_id: str
    onboarding_date: str
    branch_id: str
    risk_score: float

class AccountSchema(TypedDict):
    account_id: str
    customer_id: str
    account_type: str
    branch_id: str
    open_date: str
    currency: str
    status: str
    current_balance: float
    avg_monthly_balance: float
    linked_accounts: str

class DeviceSchema(TypedDict):
    device_id: str
    customer_id: str
    device_type: str
    os: str
    first_seen_date: str
    is_shared_device: bool

class BeneficiarySchema(TypedDict):
    beneficiary_id: str
    customer_id: str
    beneficiary_name: str
    relationship_type: str
    country_code: str
    added_date: str

class MerchantSchema(TypedDict):
    merchant_id: str
    merchant_name: str
    mcc_code: str
    category: str
    country_code: str
    risk_level: str

class LocationSchema(TypedDict):
    location_id: str
    city: str
    country_code: str
    latitude: float
    longitude: float
    is_high_risk: bool

class BranchSchema(TypedDict):
    branch_id: str
    branch_name: str
    country_code: str
    city: str
    is_high_risk_branch: bool

class CountryRiskSchema(TypedDict):
    country_code: str
    country_name: str
    fatf_status: str
    risk_score: float

class RelationshipSchema(TypedDict):
    relationship_id: str
    customer_id_1: str
    customer_id_2: str
    relationship_type: str
    is_symmetric: bool

class FraudRingSchema(TypedDict):
    fraud_ring_id: str
    ring_name: str
    ring_type: str
    formation_date: str
    num_members: int

class FraudRingMembershipSchema(TypedDict):
    membership_id: str
    fraud_ring_id: str
    customer_id: str
    role: str

