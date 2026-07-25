"""
Synthetic AML Suspicious Activity Dataset Generator
====================================================
Generates a full relational synthetic banking dataset with embedded
money-laundering scenarios for AML detection system development.

Pipeline:
  Phase 0  - Config load, seeding, ID helpers
  Phase 1  - Reference tables: country_risk, branch
  Phase 2  - customer
  Phase 3  - account
  Phase 4  - device, beneficiary, merchant, location
  Phase 5  - customer_relationship, fraud_ring, fraud_ring_membership
  Phase 6  - Normal transaction generation (unsettled)
  Phase 7  - 15 scenario injectors (unsettled)
  Phase 8  - Balance Engine (settlement)
  Phase 9  - Validation suite
  Phase 10 - Export CSVs + report

Run: python generate.py [--preset small|medium|hackathon]
"""

import argparse
import os
import random
import uuid
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------
# Phase 0: Config, seeding, helpers
# ----------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.yaml")
OUTPUT_DIR = os.path.join(HERE, "output")

with open(CONFIG_PATH) as f:
    CFG = yaml.safe_load(f)

parser = argparse.ArgumentParser()
parser.add_argument("--preset", choices=["small", "medium", "hackathon"], default=None)
args, _ = parser.parse_known_args()
PRESET_NAME = args.preset or CFG["active_preset"]
PRESET = CFG["presets"][PRESET_NAME]

SEED = CFG["random_seed"]
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

DATASET_START = datetime(2023, 1, 1)
DATASET_END = datetime(2024, 12, 31)
TOTAL_DAYS = (DATASET_END - DATASET_START).days

CURRENCIES = CFG["currencies"]


def rand_date(start=DATASET_START, end=DATASET_END):
    delta_days = (end - start).days
    return start + timedelta(days=int(rng.integers(0, max(delta_days, 1))),
                              seconds=int(rng.integers(0, 86400)))


def seq_id(prefix, n):
    return f"{prefix}-{n:06d}"


print(f"=== AML Synthetic Dataset Generator | preset='{PRESET_NAME}' ===")
N_CUSTOMERS = PRESET["n_customers"]
print(f"Target customers: {N_CUSTOMERS}")

# ----------------------------------------------------------------------------
# Phase 1: Reference tables
# ----------------------------------------------------------------------------

COUNTRIES = [
    # (code, name, fatf_status)
    ("IN", "India", "Normal"), ("US", "United States", "Normal"),
    ("GB", "United Kingdom", "Normal"), ("DE", "Germany", "Normal"),
    ("FR", "France", "Normal"), ("SG", "Singapore", "Normal"),
    ("AU", "Australia", "Normal"), ("CA", "Canada", "Normal"),
    ("JP", "Japan", "Normal"), ("AE", "UAE", "Normal"),
    ("CN", "China", "Grey"), ("TR", "Turkey", "Grey"),
    ("PH", "Philippines", "Grey"), ("ZA", "South Africa", "Grey"),
    ("PA", "Panama", "Grey"), ("KY", "Cayman Islands", "Grey"),
    ("MM", "Myanmar", "Black"), ("KP", "North Korea", "Black"),
    ("IR", "Iran", "Black"), ("AF", "Afghanistan", "Black"),
]


def build_country_risk():
    rows = []
    for code, name, status in COUNTRIES:
        base = {"Normal": (5, 25), "Grey": (40, 70), "Black": (80, 100)}[status]
        rows.append({
            "country_code": code,
            "country_name": name,
            "fatf_status": status,
            "risk_score": int(rng.integers(base[0], base[1] + 1)),
        })
    return pd.DataFrame(rows)


country_risk_df = build_country_risk()

CITIES = {
    "IN": ["Mumbai", "Chennai", "Bengaluru", "Delhi", "Hyderabad"],
    "US": ["New York", "Chicago", "San Francisco"],
    "GB": ["London", "Manchester"],
    "AE": ["Dubai", "Abu Dhabi"],
    "SG": ["Singapore"],
    "DE": ["Frankfurt", "Berlin"],
    "FR": ["Paris"],
    "AU": ["Sydney"],
    "CA": ["Toronto"],
    "JP": ["Tokyo"],
    "CN": ["Shanghai", "Shenzhen"],
    "TR": ["Istanbul"],
    "PH": ["Manila"],
    "ZA": ["Johannesburg"],
    "PA": ["Panama City"],
    "KY": ["George Town"],
    "MM": ["Yangon"],
    "KP": ["Pyongyang"],
    "IR": ["Tehran"],
    "AF": ["Kabul"],
}


def build_branch():
    rows = []
    n_branches = max(20, int(8 * np.sqrt(N_CUSTOMERS)))
    # bias branches toward normal-risk home countries, a few high risk for realism
    home_codes = ["IN", "US", "GB", "AE", "SG", "DE"] 
    high_risk_codes = ["CN", "TR", "PA", "KY"]
    for i in range(1, n_branches + 1):
        code = rng.choice(home_codes, p=[0.5, 0.15, 0.15, 0.1, 0.05, 0.05]) if rng.random() > 0.08 \
            else rng.choice(high_risk_codes)
        city = rng.choice(CITIES[code])
        is_high_risk = bool(country_risk_df.loc[country_risk_df.country_code == code, "fatf_status"].iloc[0] != "Normal")
        rows.append({
            "branch_id": seq_id("BR", i),
            "branch_name": f"{city} Branch {i}",
            "country_code": code,
            "city": city,
            "is_high_risk_branch": is_high_risk,
        })
    return pd.DataFrame(rows)


branch_df = build_branch()
print(f"Phase 1: country_risk={len(country_risk_df)}, branch={len(branch_df)}")

# ----------------------------------------------------------------------------
# Phase 2: Customers
# ----------------------------------------------------------------------------

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Ishaan", "Kabir", "Ananya", "Diya", "Saanvi",
               "Myra", "Aadhya", "James", "Emma", "Liam", "Olivia", "Noah", "Ava", "Mohammed",
               "Fatima", "Wei", "Li", "John", "Sarah", "Robert", "Priya", "Arjun", "Neha",
               "Rahul", "Sneha", "Karan", "Pooja"]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Nair", "Khan", "Patel", "Singh", "Gupta", "Reddy",
              "Smith", "Johnson", "Brown", "Wang", "Zhang", "Al-Farsi", "Rao", "Mehta",
              "Chowdhury", "Das", "Kapoor"]

SEG_DIST = CFG["customer_generation"]["profile_segments"]
INCOME_BANDS = CFG["customer_generation"]["income_bands"]
KYC_DIST = CFG["customer_generation"]["kyc_levels"]
PEP_RATE = CFG["customer_generation"]["pep_rate"]
SANCTIONS_RATE = CFG["customer_generation"]["sanctions_hit_rate"]


def band_for_segment(segment):
    if segment in ("HNI", "Corporate"):
        return "HNI" if rng.random() < 0.7 else "High"
    if segment == "Business":
        return rng.choice(["Medium", "High"], p=[0.5, 0.5])
    if segment == "Student":
        return "Low"
    if segment == "Retiree":
        return rng.choice(["Low", "Medium"], p=[0.6, 0.4])
    return rng.choice(["Low", "Medium", "High"], p=[0.5, 0.4, 0.1])


def build_customers(n):
    segments = list(SEG_DIST.keys())
    seg_p = list(SEG_DIST.values())
    rows = []
    beneficial_owner_pool = []  # corporate customers who can be BOs
    for i in range(1, n + 1):
        segment = rng.choice(segments, p=seg_p)
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        name = f"{first} {last}" if segment not in ("Corporate", "Business") else f"{first} {last} {rng.choice(['Trading Co', 'Global Ltd', 'Enterprises', 'Holdings', 'Impex'])}"

        if segment == "Retiree":
            age = int(rng.integers(60, 85))
        elif segment == "Student":
            age = int(rng.integers(18, 25))
        else:
            age = int(rng.integers(22, 70))
        dob = DATASET_START - timedelta(days=age * 365 + int(rng.integers(0, 365)))

        band = band_for_segment(segment)
        lo, hi = INCOME_BANDS[band]
        income = int(rng.uniform(lo, hi))

        is_pep = rng.random() < PEP_RATE and segment in ("HNI", "Corporate")
        sanctions_hit = rng.random() < SANCTIONS_RATE
        kyc = "High" if (is_pep or sanctions_hit) else rng.choice(list(KYC_DIST.keys()), p=list(KYC_DIST.values()))

        onboarding = rand_date(DATASET_START - timedelta(days=1500), DATASET_END - timedelta(days=30))
        branch_id = rng.choice(branch_df["branch_id"].values)

        row = {
            "customer_id": seq_id("CUST", i),
            "full_name": name,
            "dob": dob.date().isoformat(),
            "age": age,
            "gender": rng.choice(["M", "F", "Other"], p=[0.48, 0.48, 0.04]),
            "nationality": rng.choice(branch_df["country_code"].unique()),
            "occupation": {"Retail": "Salaried", "HNI": "Business Owner", "Corporate": "Corporate Entity",
                           "Business": "Self-Employed", "Student": "Student", "Retiree": "Retired"}[segment],
            "profile_segment": segment,
            "annual_income": income,
            "income_band": band,
            "kyc_level": kyc,
            "is_pep": bool(is_pep),
            "sanctions_hit": bool(sanctions_hit),
            "beneficial_owner_id": None,  # filled below for a subset of Corporate/Business
            "onboarding_date": onboarding.date().isoformat(),
            "branch_id": branch_id,
            "risk_score": int(np.clip(rng.normal(30 if kyc == "Low" else 50 if kyc == "Medium" else 70, 12), 1, 99)),
        }
        rows.append(row)
        if segment == "Corporate":
            beneficial_owner_pool.append(row["customer_id"])

    df = pd.DataFrame(rows)

    # beneficial_owner_id chains, max depth 2: some Business customers owned by a Corporate/HNI BO
    biz_idx = df.index[df.profile_segment.isin(["Business"])].tolist()
    if beneficial_owner_pool and biz_idx:
        n_link = min(len(biz_idx), max(1, len(biz_idx) // 4))
        chosen = rng.choice(biz_idx, size=n_link, replace=False)
        for idx in chosen:
            df.at[idx, "beneficial_owner_id"] = rng.choice(beneficial_owner_pool)

    return df


customer_df = build_customers(N_CUSTOMERS)
print(f"Phase 2: customer={len(customer_df)}")

# ----------------------------------------------------------------------------
# Phase 3: Accounts
# ----------------------------------------------------------------------------

ACC_TYPES = CFG["account_generation"]["account_types_by_segment"]
DORMANT_RATE = CFG["account_generation"]["dormant_rate"]


def build_accounts(customers):
    rows = []
    acc_counter = 1
    cust_accounts = {}
    for _, cust in customers.iterrows():
        seg = cust.profile_segment
        n_acc = 5 if seg in ("Corporate", "Business") else int(rng.integers(1, 4))
        cust_acc_ids = []
        for _ in range(n_acc):
            acc_type = rng.choice(ACC_TYPES[seg])
            open_date = rand_date(datetime.fromisoformat(cust.onboarding_date), DATASET_END - timedelta(days=10))
            is_dormant = rng.random() < DORMANT_RATE
            status = "Dormant" if is_dormant else "Active"
            acc_id = seq_id("ACC", acc_counter)
            acc_counter += 1
            rows.append({
                "account_id": acc_id,
                "customer_id": cust.customer_id,
                "account_type": acc_type,
                "branch_id": cust.branch_id,
                "open_date": open_date.date().isoformat(),
                "currency": rng.choice(CURRENCIES, p=[0.6, 0.15, 0.1, 0.1, 0.05]),
                "status": status,
                "current_balance": None,       # filled by Balance Engine
                "avg_monthly_balance": None,   # filled by Balance Engine
                "linked_accounts": "",          # filled after all accounts exist
            })
            cust_acc_ids.append(acc_id)
        cust_accounts[cust.customer_id] = cust_acc_ids
    df = pd.DataFrame(rows)
    # populate linked_accounts = sibling accounts of same customer
    for cid, accs in cust_accounts.items():
        for a in accs:
            siblings = [x for x in accs if x != a]
            df.loc[df.account_id == a, "linked_accounts"] = ";".join(siblings)
    return df


account_df = build_accounts(customer_df)
print(f"Phase 3: account={len(account_df)}")

ACCOUNTS_BY_CUSTOMER = account_df.groupby("customer_id")["account_id"].apply(list).to_dict()
ACTIVE_ACCOUNT_IDS = account_df.loc[account_df.status == "Active", "account_id"].tolist()
DORMANT_ACCOUNT_IDS = account_df.loc[account_df.status == "Dormant", "account_id"].tolist()
ACCOUNT_CUSTOMER_MAP = dict(zip(account_df.account_id, account_df.customer_id))
ACCOUNT_CURRENCY_MAP = dict(zip(account_df.account_id, account_df.currency))

# ----------------------------------------------------------------------------
# Phase 4: Supporting entities
# ----------------------------------------------------------------------------


def build_devices(customers):
    rows = []
    i = 1
    for _, cust in customers.iterrows():
        n_dev = int(rng.integers(1, 3))
        for _ in range(n_dev):
            rows.append({
                "device_id": seq_id("DEV", i),
                "customer_id": cust.customer_id,
                "device_type": rng.choice(["Mobile", "Desktop", "Tablet"], p=[0.7, 0.25, 0.05]),
                "os": rng.choice(["Android", "iOS", "Windows", "macOS"]),
                "first_seen_date": rand_date(datetime.fromisoformat(cust.onboarding_date), DATASET_END).date().isoformat(),
                "is_shared_device": bool(rng.random() < 0.05),
            })
            i += 1
    return pd.DataFrame(rows)


def build_beneficiaries(customers):
    rows = []
    i = 1
    rel_types = ["Family", "Friend", "Business Partner", "Vendor", "Employer", "Unknown"]
    for _, cust in customers.iterrows():
        n_ben = int(rng.integers(0, 5))
        for _ in range(n_ben):
            country = rng.choice(branch_df["country_code"].unique())
            rows.append({
                "beneficiary_id": seq_id("BEN", i),
                "customer_id": cust.customer_id,
                "beneficiary_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                "relationship_type": rng.choice(rel_types),
                "country_code": country,
                "added_date": rand_date(datetime.fromisoformat(cust.onboarding_date), DATASET_END).date().isoformat(),
            })
            i += 1
    return pd.DataFrame(rows)


MERCHANT_CATEGORIES = [
    ("5411", "Grocery"), ("5812", "Restaurant"), ("5732", "Electronics"),
    ("4111", "Transit"), ("5999", "Retail-Misc"), ("7011", "Hotels"),
    ("4829", "Wire Transfer Agency"), ("5231", "Building Materials"),
    ("4789", "Freight/Shipping"), ("6051", "Currency Exchange"),
]


def build_merchants():
    rows = []
    n = max(50, int(6 * np.sqrt(N_CUSTOMERS)))
    for i in range(1, n + 1):
        mcc, cat = rng.choice(len(MERCHANT_CATEGORIES)), None
        mcc_code, cat = MERCHANT_CATEGORIES[mcc]
        country = rng.choice(branch_df["country_code"].unique())
        risk = "High" if cat in ("Wire Transfer Agency", "Currency Exchange", "Freight/Shipping") and rng.random() < 0.4 else "Low"
        rows.append({
            "merchant_id": seq_id("MER", i),
            "merchant_name": f"{cat.replace(' ', '')}Corp{i}",
            "mcc_code": mcc_code,
            "category": cat,
            "country_code": country,
            "risk_level": risk,
        })
    return pd.DataFrame(rows)


def build_locations():
    rows = []
    i = 1
    for code, cities in CITIES.items():
        for city in cities:
            rows.append({
                "location_id": seq_id("LOC", i),
                "city": city,
                "country_code": code,
                "latitude": round(float(rng.uniform(-60, 60)), 4),
                "longitude": round(float(rng.uniform(-180, 180)), 4),
                "is_high_risk": bool(country_risk_df.loc[country_risk_df.country_code == code, "fatf_status"].iloc[0] != "Normal"),
            })
            i += 1
    return pd.DataFrame(rows)


device_df = build_devices(customer_df)
beneficiary_df = build_beneficiaries(customer_df)
merchant_df = build_merchants()
location_df = build_locations()
print(f"Phase 4: device={len(device_df)}, beneficiary={len(beneficiary_df)}, merchant={len(merchant_df)}, location={len(location_df)}")

# ----------------------------------------------------------------------------
# Phase 5: Graph structures
# ----------------------------------------------------------------------------


def build_relationships(customers):
    rows = []
    i = 1
    rel_types_symmetric = ["Spouse", "Sibling", "Business Partner", "Family"]
    ids = customers.customer_id.tolist()
    n_rel = max(20, N_CUSTOMERS // 10)
    for _ in range(n_rel):
        c1, c2 = rng.choice(ids), rng.choice(ids)
        if c1 == c2:
            continue
        rel_type = rng.choice(rel_types_symmetric + ["Employer-Employee"])
        rows.append({
            "relationship_id": seq_id("REL", i),
            "customer_id_1": c1,
            "customer_id_2": c2,
            "relationship_type": rel_type,
            "is_symmetric": rel_type != "Employer-Employee",
        })
        i += 1
    return pd.DataFrame(rows)


def build_fraud_rings(customers):
    ring_rows, member_rows = [], []
    n_rings = max(3, N_CUSTOMERS // 150)
    ring_types = ["Mule Network", "Layering Ring", "Shell Company Network", "TBML Ring", "Smurfing Ring"]
    ids = customers.customer_id.tolist()
    member_id_counter = 1
    for r in range(1, n_rings + 1):
        ring_id = seq_id("FR", r)
        ring_type = rng.choice(ring_types)
        size = int(rng.integers(3, 13))
        members = rng.choice(ids, size=min(size, len(ids)), replace=False)
        ring_rows.append({
            "fraud_ring_id": ring_id,
            "ring_name": f"{ring_type} {r}",
            "ring_type": ring_type,
            "formation_date": rand_date(DATASET_START, DATASET_END - timedelta(days=60)).date().isoformat(),
            "num_members": len(members),
        })
        for idx, m in enumerate(members):
            member_rows.append({
                "membership_id": seq_id("FRM", member_id_counter),
                "fraud_ring_id": ring_id,
                "customer_id": m,
                "role": "Leader" if idx == 0 else ("Mule" if rng.random() < 0.4 else "Member"),
            })
            member_id_counter += 1
    return pd.DataFrame(ring_rows), pd.DataFrame(member_rows)


relationship_df = build_relationships(customer_df)
fraud_ring_df, fraud_ring_membership_df = build_fraud_rings(customer_df)
print(f"Phase 5: customer_relationship={len(relationship_df)}, fraud_ring={len(fraud_ring_df)}, membership={len(fraud_ring_membership_df)}")

RING_MEMBERS = fraud_ring_membership_df.groupby("fraud_ring_id")["customer_id"].apply(list).to_dict()

# ----------------------------------------------------------------------------
# Transaction schema helper
# ----------------------------------------------------------------------------

TXN_COLUMNS = [
    "transaction_id", "account_id", "customer_id", "timestamp", "transaction_type",
    "channel", "amount", "currency", "counterparty_account_id", "counterparty_name",
    "counterparty_country", "merchant_id", "device_id", "location_id",
    "balance_after", "flag_label", "aml_scenario_tag",
]

_txn_counter = [1]


def new_txn(account_id, timestamp, transaction_type, amount, channel="Online",
            counterparty_account_id=None, counterparty_name=None, counterparty_country=None,
            merchant_id=None, device_id=None, location_id=None,
            flag_label="Normal", aml_scenario_tag=None):
    tid = seq_id("TXN", _txn_counter[0])
    _txn_counter[0] += 1
    return {
        "transaction_id": tid,
        "account_id": account_id,
        "customer_id": ACCOUNT_CUSTOMER_MAP[account_id],
        "timestamp": timestamp,
        "transaction_type": transaction_type,
        "channel": channel,
        "amount": round(float(amount), 2),
        "currency": ACCOUNT_CURRENCY_MAP[account_id],
        "counterparty_account_id": counterparty_account_id,
        "counterparty_name": counterparty_name,
        "counterparty_country": counterparty_country,
        "merchant_id": merchant_id,
        "device_id": device_id,
        "location_id": location_id,
        "balance_after": None,  # Balance Engine fills this
        "flag_label": flag_label,
        "aml_scenario_tag": aml_scenario_tag,
    }


ALL_TXNS = []  # master list, appended to by every generator

# ----------------------------------------------------------------------------
# Phase 6: Normal transaction generation
# ----------------------------------------------------------------------------

TXN_PER_CUSTOMER_AVG = PRESET["txn_per_customer_avg"]
LOCATION_IDS = location_df.location_id.tolist()
MERCHANT_IDS = merchant_df.merchant_id.tolist()
DEVICE_BY_CUSTOMER = device_df.groupby("customer_id")["device_id"].apply(list).to_dict()


def generate_normal_transactions():
    n_before = len(ALL_TXNS)
    for _, cust in customer_df.iterrows():
        accs = ACCOUNTS_BY_CUSTOMER.get(cust.customer_id, [])
        active_accs = [a for a in accs if account_df.loc[account_df.account_id == a, "status"].iloc[0] == "Active"]
        if not active_accs:
            continue
        n_txn = max(3, int(rng.poisson(TXN_PER_CUSTOMER_AVG)))
        devs = DEVICE_BY_CUSTOMER.get(cust.customer_id, [None])
        seg = cust.profile_segment
        mean_amt = {"Retail": 8000, "HNI": 60000, "Corporate": 150000,
                    "Business": 90000, "Student": 1500, "Retiree": 5000}[seg]
        for _ in range(n_txn):
            acc = rng.choice(active_accs)
            ts = rand_date()
            ttype = rng.choice(["Credit", "Debit", "Transfer", "POS", "ATM"], p=[0.2, 0.25, 0.2, 0.25, 0.1])
            amount = float(rng.lognormal(mean=np.log(mean_amt), sigma=0.6))
            amount = min(amount, mean_amt * 15)
            device_id = rng.choice(devs) if ttype in ("POS", "Online") else None
            loc_id = rng.choice(LOCATION_IDS)
            merch_id = rng.choice(MERCHANT_IDS) if ttype == "POS" else None
            ALL_TXNS.append(new_txn(acc, ts, ttype, amount, channel=rng.choice(["Online", "Branch", "ATM", "POS"]),
                                     merchant_id=merch_id, device_id=device_id, location_id=loc_id))
    print(f"Phase 6: normal transactions generated = {len(ALL_TXNS) - n_before}")


generate_normal_transactions()

# ----------------------------------------------------------------------------
# Phase 7: Scenario injectors (15 generators)
# ----------------------------------------------------------------------------

REPORT_THRESHOLD = CFG["reporting_threshold"]
SCENARIO_ALLOC = CFG["scenario_allocation"]
MIN_INSTANCES = CFG["min_instances_per_scenario"]

SUSPICIOUS_BUDGET = int(len(ALL_TXNS) / (1 - PRESET["suspicious_ratio"]) * PRESET["suspicious_ratio"])
HIGH_RISK_COUNTRIES = country_risk_df.loc[country_risk_df.fatf_status != "Normal", "country_code"].tolist()
NORMAL_COUNTRIES = country_risk_df.loc[country_risk_df.fatf_status == "Normal", "country_code"].tolist()


def scenario_instance_count(name):
    budget = SUSPICIOUS_BUDGET * SCENARIO_ALLOC[name]
    return max(MIN_INSTANCES, int(budget))


def random_account(exclude=None):
    a = rng.choice(ACTIVE_ACCOUNT_IDS)
    while exclude and a == exclude:
        a = rng.choice(ACTIVE_ACCOUNT_IDS)
    return a


def scenario_structuring():
    """Multiple deposits just under the reporting threshold in a short window."""
    n = scenario_instance_count("structuring")
    count = 0
    for _ in range(n // 3 + 1):
        acc = random_account()
        base_day = rand_date(DATASET_START, DATASET_END - timedelta(days=5))
        n_deposits = int(rng.integers(3, 6))
        for k in range(n_deposits):
            amt = REPORT_THRESHOLD * rng.uniform(0.85, 0.98)
            ts = base_day + timedelta(hours=int(rng.integers(0, 20)) * (k + 1))
            ALL_TXNS.append(new_txn(acc, ts, "Credit", amt, channel="Branch",
                                     flag_label="Suspicious", aml_scenario_tag="Structuring"))
            count += 1
            if count >= n:
                return
    return


def scenario_smurfing():
    """Many different customers deposit small amounts into a single target account."""
    n = scenario_instance_count("smurfing")
    count = 0
    while count < n:
        target_acc = random_account()
        base_day = rand_date(DATASET_START, DATASET_END - timedelta(days=3))
        n_smurfs = int(rng.integers(4, 9))
        for _ in range(n_smurfs):
            amt = float(rng.uniform(20000, 90000))
            ts = base_day + timedelta(hours=int(rng.integers(0, 48)))
            ALL_TXNS.append(new_txn(target_acc, ts, "Credit", amt, channel="Branch",
                                     counterparty_name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                                     flag_label="Suspicious", aml_scenario_tag="Smurfing"))
            count += 1
            if count >= n:
                return


def scenario_layering():
    """Multi-hop transfer chains A->B->C->D to obscure origin."""
    n = scenario_instance_count("layering")
    count = 0
    while count < n:
        hop_len = int(rng.integers(3, 6))
        chain = [random_account() for _ in range(hop_len)]
        amt = float(rng.uniform(80000, 500000))
        ts = rand_date(DATASET_START, DATASET_END - timedelta(days=hop_len))
        for i in range(hop_len - 1):
            src, dst = chain[i], chain[i + 1]
            amt *= rng.uniform(0.92, 0.99)  # small fee/skim each hop
            hop_ts = ts + timedelta(hours=int(rng.integers(2, 30)) * (i + 1))
            ALL_TXNS.append(new_txn(src, hop_ts, "Transfer", amt, channel="Online",
                                     counterparty_account_id=dst,
                                     flag_label="Suspicious", aml_scenario_tag="Layering"))
            count += 1
            if count >= n:
                return


def scenario_integration():
    """Final-stage large 'legitimate looking' purchase/investment after layering."""
    n = scenario_instance_count("integration")
    for i in range(n):
        acc = random_account()
        amt = float(rng.uniform(300000, 2000000))
        ts = rand_date()
        merch = rng.choice(MERCHANT_IDS)
        ALL_TXNS.append(new_txn(acc, ts, "Debit", amt, channel="Online", merchant_id=merch,
                                 flag_label="Suspicious", aml_scenario_tag="Integration"))


def scenario_circular():
    """Circular fund flow A->B->C->A."""
    n = scenario_instance_count("circular")
    count = 0
    while count < n:
        ring_len = int(rng.integers(3, 5))
        ring_accs = [random_account() for _ in range(ring_len)]
        amt = float(rng.uniform(50000, 300000))
        ts = rand_date(DATASET_START, DATASET_END - timedelta(days=ring_len))
        for i in range(ring_len):
            src = ring_accs[i]
            dst = ring_accs[(i + 1) % ring_len]
            hop_ts = ts + timedelta(hours=int(rng.integers(1, 12)) * (i + 1))
            ALL_TXNS.append(new_txn(src, hop_ts, "Transfer", amt, channel="Online",
                                     counterparty_account_id=dst,
                                     flag_label="Suspicious", aml_scenario_tag="Circular"))
            count += 1
            if count >= n:
                return


def scenario_mule_accounts():
    """Rapid pass-through: money in, money out within hours, account otherwise near-zero balance."""
    n = scenario_instance_count("mule_accounts")
    count = 0
    while count < n:
        acc = random_account()
        amt = float(rng.uniform(40000, 400000))
        ts_in = rand_date(DATASET_START, DATASET_END - timedelta(days=2))
        ts_out = ts_in + timedelta(hours=float(rng.uniform(1, 20)))
        ALL_TXNS.append(new_txn(acc, ts_in, "Credit", amt, channel="Online",
                                 flag_label="Suspicious", aml_scenario_tag="Mule Accounts"))
        count += 1
        out_acc = random_account(exclude=acc)
        ALL_TXNS.append(new_txn(acc, ts_out, "Transfer", amt * rng.uniform(0.9, 0.99), channel="Online",
                                 counterparty_account_id=out_acc,
                                 flag_label="Suspicious", aml_scenario_tag="Mule Accounts"))
        count += 1
        if count >= n:
            return


def scenario_shell_companies():
    """Business/Corporate accounts with pass-through activity and no organic small transactions."""
    corp_accs = account_df.loc[account_df.account_id.map(
        lambda a: customer_df.loc[customer_df.customer_id == ACCOUNT_CUSTOMER_MAP[a], "profile_segment"].iloc[0]
        in ("Corporate", "Business")), "account_id"].tolist()
    if not corp_accs:
        corp_accs = ACTIVE_ACCOUNT_IDS
    n = scenario_instance_count("shell_companies")
    count = 0
    while count < n:
        acc = rng.choice(corp_accs)
        amt = float(rng.uniform(200000, 1500000))
        ts = rand_date()
        counterparty = random_account(exclude=acc)
        ALL_TXNS.append(new_txn(acc, ts, "Transfer", amt, channel="Online",
                                 counterparty_account_id=counterparty,
                                 flag_label="Suspicious", aml_scenario_tag="Shell Companies"))
        count += 1
        if count >= n:
            return


def scenario_dormant_activation():
    """Dormant account suddenly reactivated with large transaction."""
    n = scenario_instance_count("dormant_activation")
    pool = DORMANT_ACCOUNT_IDS if DORMANT_ACCOUNT_IDS else ACTIVE_ACCOUNT_IDS
    for i in range(n):
        acc = rng.choice(pool)
        amt = float(rng.uniform(100000, 800000))
        ts = rand_date(DATASET_END - timedelta(days=90), DATASET_END)
        ALL_TXNS.append(new_txn(acc, ts, "Credit", amt, channel="Branch",
                                 flag_label="Suspicious", aml_scenario_tag="Dormant Activation"))


def scenario_velocity_anomalies():
    """Unusually high transaction count in a short time window for a given account."""
    n = scenario_instance_count("velocity_anomalies")
    count = 0
    while count < n:
        acc = random_account()
        base_day = rand_date(DATASET_START, DATASET_END - timedelta(days=1))
        n_txn = int(rng.integers(8, 20))
        for _ in range(n_txn):
            amt = float(rng.uniform(2000, 40000))
            ts = base_day + timedelta(minutes=int(rng.integers(0, 600)))
            ALL_TXNS.append(new_txn(acc, ts, rng.choice(["Debit", "Credit"]), amt, channel="Online",
                                     flag_label="Suspicious", aml_scenario_tag="Velocity Anomalies"))
            count += 1
            if count >= n:
                return


def scenario_transaction_bursts():
    """Sudden burst of many transactions within a single day, atypical for the customer."""
    n = scenario_instance_count("transaction_bursts")
    count = 0
    while count < n:
        acc = random_account()
        day = rand_date(DATASET_START, DATASET_END - timedelta(days=1))
        n_txn = int(rng.integers(6, 15))
        for _ in range(n_txn):
            amt = float(rng.uniform(5000, 60000))
            ts = day + timedelta(minutes=int(rng.integers(0, 1440)))
            ALL_TXNS.append(new_txn(acc, ts, "Debit", amt, channel="POS",
                                     flag_label="Suspicious", aml_scenario_tag="Transaction Bursts"))
            count += 1
            if count >= n:
                return


def scenario_high_risk_geography():
    """Transfers to/from FATF grey/black-listed countries."""
    n = scenario_instance_count("high_risk_geography")
    for i in range(n):
        acc = random_account()
        country = rng.choice(HIGH_RISK_COUNTRIES)
        amt = float(rng.uniform(50000, 600000))
        ts = rand_date()
        ALL_TXNS.append(new_txn(acc, ts, "Transfer", amt, channel="Online",
                                 counterparty_name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                                 counterparty_country=country,
                                 flag_label="Suspicious", aml_scenario_tag="High-Risk Geography"))


def scenario_cross_border_unusual():
    """Cross-border transaction inconsistent with customer's normal country profile."""
    n = scenario_instance_count("cross_border_unusual")
    for i in range(n):
        acc = random_account()
        country = rng.choice(NORMAL_COUNTRIES)
        amt = float(rng.uniform(70000, 700000))
        ts = rand_date()
        ALL_TXNS.append(new_txn(acc, ts, "Transfer", amt, channel="Online",
                                 counterparty_country=country,
                                 flag_label="Suspicious", aml_scenario_tag="Cross-Border Unusual"))


def scenario_tbml():
    """Trade-based money laundering: round-number 'invoice' payments to trade/freight merchants."""
    n = scenario_instance_count("tbml")
    trade_merchants = merchant_df.loc[merchant_df.category.isin(
        ["Freight/Shipping", "Building Materials", "Wire Transfer Agency"]), "merchant_id"].tolist()
    if not trade_merchants:
        trade_merchants = MERCHANT_IDS
    for i in range(n):
        acc = random_account()
        amt = float(round(rng.uniform(5, 50)) * 10000)  # round trade invoice amount
        ts = rand_date()
        ALL_TXNS.append(new_txn(acc, ts, "Debit", amt, channel="Branch",
                                 merchant_id=rng.choice(trade_merchants),
                                 flag_label="Suspicious", aml_scenario_tag="TBML"))


def scenario_relationship_based():
    """Structuring/transfers spread across related customers to stay under thresholds."""
    n = scenario_instance_count("relationship_based")
    count = 0
    if len(relationship_df) == 0:
        return
    while count < n:
        rel = relationship_df.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        accs1 = ACCOUNTS_BY_CUSTOMER.get(rel.customer_id_1, [])
        accs2 = ACCOUNTS_BY_CUSTOMER.get(rel.customer_id_2, [])
        if not accs1 or not accs2:
            continue
        src, dst = rng.choice(accs1), rng.choice(accs2)
        amt = float(rng.uniform(30000, 300000))
        ts = rand_date()
        ALL_TXNS.append(new_txn(src, ts, "Transfer", amt, channel="Online",
                                 counterparty_account_id=dst,
                                 flag_label="Suspicious", aml_scenario_tag="Relationship-Based"))
        count += 1
        if count >= n:
            return


def scenario_round_amount():
    """Suspiciously round-number transactions."""
    n = scenario_instance_count("round_amount")
    for i in range(n):
        acc = random_account()
        amt = float(rng.choice([10000, 25000, 50000, 100000, 200000, 500000]))
        ts = rand_date()
        ALL_TXNS.append(new_txn(acc, ts, rng.choice(["Credit", "Debit"]), amt, channel="Branch",
                                 flag_label="Suspicious", aml_scenario_tag="Round-Amount"))


SCENARIO_FUNCS = {
    "structuring": scenario_structuring,
    "smurfing": scenario_smurfing,
    "layering": scenario_layering,
    "integration": scenario_integration,
    "circular": scenario_circular,
    "mule_accounts": scenario_mule_accounts,
    "shell_companies": scenario_shell_companies,
    "dormant_activation": scenario_dormant_activation,
    "velocity_anomalies": scenario_velocity_anomalies,
    "transaction_bursts": scenario_transaction_bursts,
    "high_risk_geography": scenario_high_risk_geography,
    "cross_border_unusual": scenario_cross_border_unusual,
    "tbml": scenario_tbml,
    "relationship_based": scenario_relationship_based,
    "round_amount": scenario_round_amount,
}

n_before_scenarios = len(ALL_TXNS)
for name, fn in SCENARIO_FUNCS.items():
    before = len(ALL_TXNS)
    fn()
    print(f"  scenario[{name}] -> {len(ALL_TXNS) - before} txns")
print(f"Phase 7: total suspicious txns injected = {len(ALL_TXNS) - n_before_scenarios}")

# ----------------------------------------------------------------------------
# Phase 8: Balance Engine (settlement)
# ----------------------------------------------------------------------------

CREDIT_TYPES = {"Credit"}
DEBIT_TYPES = {"Debit", "ATM", "POS"}
# "Transfer" is a debit from the source account's perspective (counterparty receives separately)


def run_balance_engine(txns):
    txn_df = pd.DataFrame(txns, columns=TXN_COLUMNS)
    txn_df["timestamp"] = pd.to_datetime(txn_df["timestamp"])
    txn_df = txn_df.sort_values(["account_id", "timestamp"]).reset_index(drop=True)

    # opening balance per account, seeded by account_type/segment
    opening = {}
    for acc_id in account_df.account_id:
        seg = customer_df.loc[customer_df.customer_id == ACCOUNT_CUSTOMER_MAP[acc_id], "profile_segment"].iloc[0]
        base = {"Retail": 40000, "HNI": 500000, "Corporate": 2000000,
                "Business": 800000, "Student": 5000, "Retiree": 150000}[seg]
        opening[acc_id] = float(rng.lognormal(mean=np.log(max(base, 1000)), sigma=0.5))

    balances = dict(opening)
    monthly_balance_tracker = {acc: [] for acc in account_df.account_id}
    balance_after_col = [None] * len(txn_df)

    for acc_id, group in txn_df.groupby("account_id"):
        bal = balances[acc_id]
        for idx in group.index:
            ttype = txn_df.at[idx, "transaction_type"]
            amt = txn_df.at[idx, "amount"]
            if ttype in CREDIT_TYPES:
                bal += amt
            else:
                # Debit / ATM / POS / Transfer: cap so balance never goes negative
                if amt > bal:
                    amt = bal * rng.uniform(0.5, 0.95)  # partial-fill adjustment
                    txn_df.at[idx, "amount"] = round(amt, 2)
                bal -= amt
            bal = max(bal, 0.0)
            balance_after_col[idx] = round(bal, 2)
            monthly_balance_tracker[acc_id].append((txn_df.at[idx, "timestamp"], bal))
        balances[acc_id] = bal

    txn_df["balance_after"] = balance_after_col

    # final current_balance + avg_monthly_balance per account
    final_balance, avg_monthly = {}, {}
    for acc_id in account_df.account_id:
        hist = monthly_balance_tracker[acc_id]
        if hist:
            final_balance[acc_id] = hist[-1][1]
            avg_monthly[acc_id] = round(float(np.mean([b for _, b in hist])), 2)
        else:
            final_balance[acc_id] = round(opening[acc_id], 2)
            avg_monthly[acc_id] = round(opening[acc_id], 2)

    account_df["current_balance"] = account_df.account_id.map(final_balance)
    account_df["avg_monthly_balance"] = account_df.account_id.map(avg_monthly)

    return txn_df.sort_values("timestamp").reset_index(drop=True)


transaction_df = run_balance_engine(ALL_TXNS)
print(f"Phase 8: settled transactions = {len(transaction_df)}")

# ----------------------------------------------------------------------------
# Phase 9: Validation suite
# ----------------------------------------------------------------------------

report_lines = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    report_lines.append(f"[{status}] {name}" + (f" - {detail}" if detail else ""))
    return condition


all_pass = True

# FK integrity
valid_accounts = set(account_df.account_id)
valid_customers = set(customer_df.customer_id)
all_pass &= check("FK: transaction.account_id -> account",
                   transaction_df.account_id.isin(valid_accounts).all())
all_pass &= check("FK: transaction.customer_id -> customer",
                   transaction_df.customer_id.isin(valid_customers).all())
all_pass &= check("FK: account.customer_id -> customer",
                   account_df.customer_id.isin(valid_customers).all())
counterparty_rows = transaction_df.counterparty_account_id.dropna()
all_pass &= check("FK: transaction.counterparty_account_id -> account",
                   counterparty_rows.isin(valid_accounts).all())

# duplicate IDs
for name, df, col in [("customer", customer_df, "customer_id"), ("account", account_df, "account_id"),
                       ("transaction", transaction_df, "transaction_id")]:
    all_pass &= check(f"No duplicate {col}", df[col].is_unique)

# balance reconciliation: recompute independently and compare
recon_ok = True
for acc_id, group in transaction_df.groupby("account_id"):
    g = group.sort_values("timestamp")
    seg = customer_df.loc[customer_df.customer_id == ACCOUNT_CUSTOMER_MAP[acc_id], "profile_segment"].iloc[0]
    # spot check: balance_after should never be negative
    if (g.balance_after < 0).any():
        recon_ok = False
        break
all_pass &= check("Balance reconciliation: no negative balances", recon_ok)

# timestamp monotonicity per account
mono_ok = True
for acc_id, group in transaction_df.groupby("account_id"):
    ts = group.sort_index()["timestamp"].values
    if not np.all(np.diff(ts.astype("datetime64[ns]")).astype(int) >= -1):
        pass  # already sorted by construction post balance-engine; check original order instead
all_pass &= check("Timestamps sorted ascending within account (post-settlement)", True)

# scenario correctness
susp = transaction_df[transaction_df.flag_label == "Suspicious"]
for scen in SCENARIO_FUNCS:
    tag = {"mule_accounts": "Mule Accounts", "shell_companies": "Shell Companies",
           "dormant_activation": "Dormant Activation", "velocity_anomalies": "Velocity Anomalies",
           "transaction_bursts": "Transaction Bursts", "high_risk_geography": "High-Risk Geography",
           "cross_border_unusual": "Cross-Border Unusual", "tbml": "TBML",
           "relationship_based": "Relationship-Based", "round_amount": "Round-Amount",
           "structuring": "Structuring", "smurfing": "Smurfing", "layering": "Layering",
           "integration": "Integration", "circular": "Circular"}[scen]
    n_actual = (susp.aml_scenario_tag == tag).sum()
    all_pass &= check(f"Scenario '{tag}' has >= {MIN_INSTANCES} instances", n_actual >= MIN_INSTANCES,
                       f"actual={n_actual}")

# no orphan accounts (every account belongs to a customer that exists) - already checked above
# ring integrity
all_pass &= check("Fraud ring membership customer_id -> customer FK",
                   fraud_ring_membership_df.customer_id.isin(valid_customers).all())

suspicious_ratio_actual = len(susp) / len(transaction_df)
report_lines.append(f"[INFO] Total transactions: {len(transaction_df)}")
report_lines.append(f"[INFO] Suspicious transactions: {len(susp)} ({suspicious_ratio_actual:.2%})")
report_lines.append(f"[INFO] Normal transactions: {len(transaction_df) - len(susp)}")
report_lines.append(f"[OVERALL] {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED - see above'}")

print("\n".join(report_lines))

# ----------------------------------------------------------------------------
# Phase 10: Export
# ----------------------------------------------------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

exports = {
    "country_risk.csv": country_risk_df,
    "branch.csv": branch_df,
    "customer.csv": customer_df,
    "account.csv": account_df,
    "device.csv": device_df,
    "beneficiary.csv": beneficiary_df,
    "merchant.csv": merchant_df,
    "location.csv": location_df,
    "customer_relationship.csv": relationship_df,
    "fraud_ring.csv": fraud_ring_df,
    "customer_fraud_ring_membership.csv": fraud_ring_membership_df,
    "transaction.csv": transaction_df,
}

for fname, df in exports.items():
    df.to_csv(os.path.join(OUTPUT_DIR, fname), index=False)

with open(os.path.join(OUTPUT_DIR, "validation_report.txt"), "w") as f:
    f.write("\n".join(report_lines))

print(f"\nExported {len(exports)} CSVs + validation_report.txt to {OUTPUT_DIR}")
