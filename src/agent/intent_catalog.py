"""
Intent Keyword Catalogue
========================
Keyword-group definitions used by IntentRecognizer.

Structure
---------
KEYWORD_CATALOGUE is a list of (Intent, weight, keyword_group) tuples:

    weight        — relative importance of this rule; higher = stronger evidence
    keyword_group — ALL tokens must appear in the normalised query to match

To extend the recognizer, add new tuples here.
No changes to IntentRecognizer are required.

Ordering convention: most-specific multi-token groups first within each
Intent block so they accumulate more weight than generic fallbacks.
"""
from __future__ import annotations

from typing import List, Tuple

from src.agent.intent_models import Intent

# Type alias: (weight, token_group)
_KWGroup = Tuple[float, Tuple[str, ...]]
CatalogueEntry = Tuple[Intent, _KWGroup]

KEYWORD_CATALOGUE: List[CatalogueEntry] = [

    # ── TRANSACTION_INVESTIGATION ─────────────────────────────────────
    (Intent.TRANSACTION_INVESTIGATION, (3.0, ("investigate", "transaction"))),
    (Intent.TRANSACTION_INVESTIGATION, (3.0, ("look", "into", "transaction"))),
    (Intent.TRANSACTION_INVESTIGATION, (2.5, ("analyze", "transaction"))),
    (Intent.TRANSACTION_INVESTIGATION, (2.5, ("analyse", "transaction"))),
    (Intent.TRANSACTION_INVESTIGATION, (2.5, ("review", "transaction"))),
    (Intent.TRANSACTION_INVESTIGATION, (2.5, ("check", "transaction"))),
    (Intent.TRANSACTION_INVESTIGATION, (2.0, ("transaction", "details"))),
    (Intent.TRANSACTION_INVESTIGATION, (1.5, ("txn",))),
    (Intent.TRANSACTION_INVESTIGATION, (1.5, ("tx",))),

    # ── CUSTOMER_INVESTIGATION ────────────────────────────────────────
    (Intent.CUSTOMER_INVESTIGATION,    (3.0, ("investigate", "customer"))),
    (Intent.CUSTOMER_INVESTIGATION,    (3.0, ("look", "into", "customer"))),
    (Intent.CUSTOMER_INVESTIGATION,    (2.5, ("analyze", "customer"))),
    (Intent.CUSTOMER_INVESTIGATION,    (2.5, ("analyse", "customer"))),
    (Intent.CUSTOMER_INVESTIGATION,    (2.5, ("review", "customer"))),
    (Intent.CUSTOMER_INVESTIGATION,    (2.5, ("check", "customer"))),
    (Intent.CUSTOMER_INVESTIGATION,    (2.0, ("customer", "profile"))),
    (Intent.CUSTOMER_INVESTIGATION,    (2.0, ("customer", "investigation"))),

    # ── HIGH_RISK_CUSTOMER ────────────────────────────────────────────
    (Intent.HIGH_RISK_CUSTOMER,        (3.0, ("high", "risk", "customer"))),
    (Intent.HIGH_RISK_CUSTOMER,        (3.0, ("flag", "high", "risk"))),
    (Intent.HIGH_RISK_CUSTOMER,        (2.5, ("high", "risk", "account"))),
    (Intent.HIGH_RISK_CUSTOMER,        (2.5, ("critical", "risk", "customer"))),
    (Intent.HIGH_RISK_CUSTOMER,        (2.5, ("risky", "customer"))),
    (Intent.HIGH_RISK_CUSTOMER,        (2.0, ("suspicious", "customer"))),
    (Intent.HIGH_RISK_CUSTOMER,        (2.0, ("flag", "customer"))),
    (Intent.HIGH_RISK_CUSTOMER,        (1.5, ("high", "risk"))),

    # ── AML_PATTERN_SEARCH ────────────────────────────────────────────
    (Intent.AML_PATTERN_SEARCH,        (3.0, ("find", "structuring", "pattern"))),
    (Intent.AML_PATTERN_SEARCH,        (3.0, ("detect", "aml", "pattern"))),
    (Intent.AML_PATTERN_SEARCH,        (2.5, ("structuring", "pattern"))),
    (Intent.AML_PATTERN_SEARCH,        (2.5, ("find", "aml", "pattern"))),
    (Intent.AML_PATTERN_SEARCH,        (2.5, ("aml", "pattern"))),
    (Intent.AML_PATTERN_SEARCH,        (2.5, ("money", "laundering", "pattern"))),
    (Intent.AML_PATTERN_SEARCH,        (2.5, ("find", "structuring"))),
    (Intent.AML_PATTERN_SEARCH,        (2.0, ("layering",))),
    (Intent.AML_PATTERN_SEARCH,        (2.0, ("smurfing",))),
    (Intent.AML_PATTERN_SEARCH,        (2.0, ("round", "tripping"))),
    (Intent.AML_PATTERN_SEARCH,        (2.0, ("mule",))),
    (Intent.AML_PATTERN_SEARCH,        (2.0, ("typology",))),
    (Intent.AML_PATTERN_SEARCH,        (1.5, ("structuring",))),
    (Intent.AML_PATTERN_SEARCH,        (1.5, ("pattern",))),

    # ── DASHBOARD_SUMMARY ─────────────────────────────────────────────
    (Intent.DASHBOARD_SUMMARY,         (3.0, ("generate", "dashboard", "summary"))),
    (Intent.DASHBOARD_SUMMARY,         (2.5, ("dashboard", "summary"))),
    (Intent.DASHBOARD_SUMMARY,         (2.5, ("executive", "summary"))),
    (Intent.DASHBOARD_SUMMARY,         (2.5, ("show", "dashboard"))),
    (Intent.DASHBOARD_SUMMARY,         (2.0, ("dashboard", "overview"))),
    (Intent.DASHBOARD_SUMMARY,         (2.0, ("overall", "summary"))),
    (Intent.DASHBOARD_SUMMARY,         (1.5, ("dashboard",))),
    (Intent.DASHBOARD_SUMMARY,         (1.5, ("summary",))),

    # ── REPORT_GENERATION ─────────────────────────────────────────────
    (Intent.REPORT_GENERATION,         (3.0, ("generate", "investigation", "report"))),
    (Intent.REPORT_GENERATION,         (3.0, ("create", "investigation", "report"))),
    (Intent.REPORT_GENERATION,         (2.5, ("generate", "report"))),
    (Intent.REPORT_GENERATION,         (2.5, ("create", "report"))),
    (Intent.REPORT_GENERATION,         (2.5, ("investigation", "report"))),
    (Intent.REPORT_GENERATION,         (2.5, ("produce", "report"))),
    (Intent.REPORT_GENERATION,         (2.5, ("export", "report"))),
    (Intent.REPORT_GENERATION,         (2.0, ("sar", "report"))),
    (Intent.REPORT_GENERATION,         (2.0, ("file", "report"))),
    (Intent.REPORT_GENERATION,         (1.5, ("report",))),

    # ── DATASET_ANALYSIS (broad — evaluated after specific intents) ───
    (Intent.DATASET_ANALYSIS,          (3.0, ("analyze", "dataset", "suspicious"))),
    (Intent.DATASET_ANALYSIS,          (3.0, ("analyse", "dataset", "suspicious"))),
    (Intent.DATASET_ANALYSIS,          (2.5, ("run", "full", "analysis"))),
    (Intent.DATASET_ANALYSIS,          (2.5, ("run", "pipeline"))),
    (Intent.DATASET_ANALYSIS,          (2.5, ("analyze", "dataset"))),
    (Intent.DATASET_ANALYSIS,          (2.5, ("analyse", "dataset"))),
    (Intent.DATASET_ANALYSIS,          (2.5, ("full", "detection"))),
    (Intent.DATASET_ANALYSIS,          (2.0, ("scan", "dataset"))),
    (Intent.DATASET_ANALYSIS,          (2.0, ("suspicious", "activity", "detection"))),
    (Intent.DATASET_ANALYSIS,          (2.0, ("detect", "suspicious"))),
    (Intent.DATASET_ANALYSIS,          (2.0, ("analyze", "transactions"))),
    (Intent.DATASET_ANALYSIS,          (1.5, ("suspicious", "activity"))),
    (Intent.DATASET_ANALYSIS,          (1.5, ("analyze",))),
    (Intent.DATASET_ANALYSIS,          (1.5, ("analyse",))),
]

# ---------------------------------------------------------------------------
# Per-intent maximum possible raw score (precomputed for normalisation)
# ---------------------------------------------------------------------------
# Used by IntentRecognizer to normalise confidence on a per-intent basis,
# ensuring that intents with fewer rules are not unfairly penalised.

def _build_max_scores() -> dict[Intent, float]:
    """Precomputes the maximum achievable raw score for each intent."""
    totals: dict[Intent, float] = {}
    for intent, (weight, _) in KEYWORD_CATALOGUE:
        totals[intent] = totals.get(intent, 0.0) + weight
    return totals


MAX_SCORE_PER_INTENT: dict[Intent, float] = _build_max_scores()
