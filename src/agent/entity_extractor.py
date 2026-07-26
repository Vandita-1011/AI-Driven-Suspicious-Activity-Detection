"""
Entity & Filter Extractor
=========================
Extracts structured entities and filters from a raw analyst query.

Design
------
All extraction is performed using compiled regular expressions.  No ML
models are required.  The extractor is stateless and thread-safe.

Extracted entities
------------------
- Customer IDs   : "customer 4521", "customer C1001"
- Transaction IDs: "transaction TX102", "txn 45001", "tx 998"
- Account IDs    : "account A100", "account 12345"
- Risk Levels    : "high risk", "medium risk", "critical risk", "low risk"
- AML Patterns   : structuring, smurfing, layering, money mule, …
- Countries      : India, UAE, Singapore, USA, United Kingdom, …
- Amount Filters : "above 100000", "less than 50k", "between 10k and 50k"
- Date Filters   : "today", "last week", "last 30 days", "this year", …
- Top/Limit      : "top 10", "top 20"

Normalisation
-------------
- Currency shorthand (k / K, m / M, cr / CR) is expanded to full numbers.
- Country names are title-cased.
- AML pattern names are lower-cased canonical strings.

Usage
-----
    from src.agent.entity_extractor import EntityExtractor

    extractor = EntityExtractor()
    result = extractor.extract("Find structuring for customer 4521 above 500000")
    print(result.customer_ids)    # ['4521']
    print(result.aml_patterns)    # ['structuring']
    print(result.amount_filters)  # [AmountFilter(operator=ABOVE, value=500000.0)]
"""
from __future__ import annotations

import re
from typing import List, Optional, Set, Tuple

from src.agent.entity_models import (
    AmountFilter,
    AmountOperator,
    DateFilter,
    EntityExtractionResult,
    RiskLevelFilter,
)
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Customer IDs — "customer 4521", "customer C1001", "cust_id C-9900"
_RE_CUSTOMER = re.compile(
    r"\b(?:customer|client|cust(?:omer)?[_\s]?id)\s+([A-Za-z0-9][A-Za-z0-9\-_]*)",
    re.IGNORECASE,
)

# Transaction IDs — "transaction TX102", "txn 45001", "tx 998"
_RE_TRANSACTION = re.compile(
    r"\b(?:transaction[_\s]?(?:id)?|txn[_\s]?(?:id)?|tx[_\s]?(?:id)?)\s+([A-Za-z0-9][A-Za-z0-9\-_]*)",
    re.IGNORECASE,
)

# Account IDs — "account A100", "account 12345", "acc_id A-9900"
_RE_ACCOUNT = re.compile(
    r"\b(?:account[_\s]?(?:id)?|acc(?:ount)?[_\s]?(?:id)?)\s+([A-Za-z0-9][A-Za-z0-9\-_]*)",
    re.IGNORECASE,
)

# Risk level
_RE_RISK_LEVEL = re.compile(
    r"\b(critical|very\s+high|high|medium|moderate|low)\s+risk\b",
    re.IGNORECASE,
)

# Top / Limit
_RE_LIMIT = re.compile(r"\btop\s+(\d+)\b", re.IGNORECASE)

# Amount shorthand: 10k → 10000, 1.5m → 1500000, 2cr → 20000000
_RE_SHORTHAND = re.compile(r"(\d+(?:\.\d+)?)\s*(k|m|cr)\b", re.IGNORECASE)

# Amount filters
_RE_AMOUNT_ABOVE = re.compile(
    r"\b(?:above|greater\s+than|more\s+than|over|exceeding|>)\s*([0-9,]+(?:\.[0-9]+)?(?:\s*(?:k|m|cr))?)\b",
    re.IGNORECASE,
)
_RE_AMOUNT_BELOW = re.compile(
    r"\b(?:below|less\s+than|under|not\s+exceeding|<)\s*([0-9,]+(?:\.[0-9]+)?(?:\s*(?:k|m|cr))?)\b",
    re.IGNORECASE,
)
_RE_AMOUNT_BETWEEN = re.compile(
    r"\bbetween\s+([0-9,]+(?:\.[0-9]+)?(?:\s*(?:k|m|cr))?)\s+and\s+([0-9,]+(?:\.[0-9]+)?(?:\s*(?:k|m|cr))?)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# AML pattern catalogue
# ---------------------------------------------------------------------------

# Maps every recognised surface form → canonical name
_AML_PATTERN_MAP: dict[str, str] = {
    "structuring":            "structuring",
    "smurfing":               "smurfing",
    "layering":               "layering",
    "money mule":             "money_mule",
    "mule account":           "money_mule",
    "mule":                   "money_mule",
    "circular transaction":   "circular_transactions",
    "circular transactions":  "circular_transactions",
    "round trip":             "circular_transactions",
    "round tripping":         "circular_transactions",
    "rapid fund movement":    "rapid_fund_movement",
    "rapid movement":         "rapid_fund_movement",
    "velocity":               "rapid_fund_movement",
    "dormant account":        "dormant_account",
    "dormant reactivation":   "dormant_account",
    "shell company":          "shell_company",
    "shell account":          "shell_company",
    "trade based":            "trade_based_laundering",
    "trade based laundering": "trade_based_laundering",
}

# Sorted longest-first so multi-word phrases match before sub-phrases
_AML_PATTERNS_SORTED: List[Tuple[str, str]] = sorted(
    _AML_PATTERN_MAP.items(), key=lambda x: len(x[0]), reverse=True
)


# ---------------------------------------------------------------------------
# Country catalogue
# ---------------------------------------------------------------------------

_KNOWN_COUNTRIES: Set[str] = {
    "india", "uae", "united arab emirates", "singapore", "usa",
    "united states", "united states of america", "united kingdom", "uk",
    "great britain", "china", "hong kong", "russia", "cayman islands",
    "british virgin islands", "panama", "switzerland", "luxembourg",
    "nigeria", "pakistan", "iran", "north korea", "myanmar", "kenya",
    "south africa", "brazil", "mexico", "canada", "germany", "france",
    "australia", "new zealand", "japan", "south korea", "malaysia",
    "indonesia", "thailand", "philippines", "bangladesh", "sri lanka",
    "nepal", "afghanistan", "iraq", "saudi arabia", "turkey", "israel",
}

# Canonical display names (lower key → display)
_COUNTRY_DISPLAY: dict[str, str] = {
    "india": "India",
    "uae": "UAE",
    "united arab emirates": "UAE",
    "singapore": "Singapore",
    "usa": "USA",
    "united states": "USA",
    "united states of america": "USA",
    "united kingdom": "United Kingdom",
    "uk": "United Kingdom",
    "great britain": "United Kingdom",
    "china": "China",
    "hong kong": "Hong Kong",
    "russia": "Russia",
    "cayman islands": "Cayman Islands",
    "british virgin islands": "British Virgin Islands",
    "panama": "Panama",
    "switzerland": "Switzerland",
    "luxembourg": "Luxembourg",
    "nigeria": "Nigeria",
    "pakistan": "Pakistan",
    "iran": "Iran",
    "north korea": "North Korea",
    "myanmar": "Myanmar",
    "kenya": "Kenya",
    "south africa": "South Africa",
    "brazil": "Brazil",
    "mexico": "Mexico",
    "canada": "Canada",
    "germany": "Germany",
    "france": "France",
    "australia": "Australia",
    "new zealand": "New Zealand",
    "japan": "Japan",
    "south korea": "South Korea",
    "malaysia": "Malaysia",
    "indonesia": "Indonesia",
    "thailand": "Thailand",
    "philippines": "Philippines",
    "bangladesh": "Bangladesh",
    "sri lanka": "Sri Lanka",
    "nepal": "Nepal",
    "afghanistan": "Afghanistan",
    "iraq": "Iraq",
    "saudi arabia": "Saudi Arabia",
    "turkey": "Turkey",
    "israel": "Israel",
}

# Sorted longest-first to match "United Arab Emirates" before "Emirates"
_COUNTRIES_SORTED: List[Tuple[str, str]] = sorted(
    _COUNTRY_DISPLAY.items(), key=lambda x: len(x[0]), reverse=True
)


# ---------------------------------------------------------------------------
# Date filter patterns
# ---------------------------------------------------------------------------

_DATE_PATTERNS: List[Tuple[str, re.Pattern[str], str]] = [
    ("today",         re.compile(r"\btoday\b",                    re.IGNORECASE), "today"),
    ("yesterday",     re.compile(r"\byesterday\b",                re.IGNORECASE), "yesterday"),
    ("last_week",     re.compile(r"\blast\s+week\b",              re.IGNORECASE), "last_week"),
    ("last_month",    re.compile(r"\blast\s+month\b",             re.IGNORECASE), "last_month"),
    ("last_year",     re.compile(r"\blast\s+year\b",              re.IGNORECASE), "last_year"),
    ("this_year",     re.compile(r"\bthis\s+year\b",              re.IGNORECASE), "this_year"),
    ("last_7_days",   re.compile(r"\blast\s+7\s+days?\b",         re.IGNORECASE), "last_7_days"),
    ("last_30_days",  re.compile(r"\blast\s+30\s+days?\b",        re.IGNORECASE), "last_30_days"),
    ("last_60_days",  re.compile(r"\blast\s+60\s+days?\b",        re.IGNORECASE), "last_60_days"),
    ("last_90_days",  re.compile(r"\blast\s+90\s+days?\b",        re.IGNORECASE), "last_90_days"),
    ("last_n_days",   re.compile(r"\blast\s+(\d+)\s+days?\b",     re.IGNORECASE), "last_n_days"),
    ("custom_range",  re.compile(
        r"\bfrom\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})\b",
        re.IGNORECASE,
    ), "custom_range"),
]

# Risk level normalisation map
_RISK_LEVEL_MAP: dict[str, RiskLevelFilter] = {
    "critical":  RiskLevelFilter.CRITICAL,
    "very high": RiskLevelFilter.CRITICAL,
    "high":      RiskLevelFilter.HIGH,
    "medium":    RiskLevelFilter.MEDIUM,
    "moderate":  RiskLevelFilter.MEDIUM,
    "low":       RiskLevelFilter.LOW,
}


# ---------------------------------------------------------------------------
# EntityExtractor
# ---------------------------------------------------------------------------

class EntityExtractor:
    """
    Extracts structured entities and filters from a raw analyst query.

    The extractor is stateless and thread-safe.  Each call to
    ``extract()`` is independent.

    Examples::

        extractor = EntityExtractor()
        result = extractor.extract("Top 10 structuring cases for customer C1001")
        print(result.customer_ids)   # ['C1001']
        print(result.aml_patterns)   # ['structuring']
        print(result.limit)          # 10
    """

    @timed("Entity Extraction")
    def extract(self, query: str) -> EntityExtractionResult:
        """
        Extracts entities and filters from *query*.

        Args:
            query: Raw natural-language analyst query.  Empty strings are
                   handled gracefully — all lists will be empty.

        Returns:
            EntityExtractionResult with all identified entities and filters.
        """
        if not query or not query.strip():
            logger.warning("EntityExtractor received an empty query.")
            return EntityExtractionResult(raw_query=query or "")

        logger.debug("Extracting entities from query: '%s'", query)

        working = query  # we progressively strip matched spans

        customer_ids  = self._extract_customers(working)
        transaction_ids = self._extract_transactions(working)
        account_ids   = self._extract_accounts(working)
        risk_level    = self._extract_risk_level(working)
        aml_patterns  = self._extract_aml_patterns(working)
        countries     = self._extract_countries(working)
        amount_filters = self._extract_amounts(working)
        date_filter   = self._extract_date(working)
        limit         = self._extract_limit(working)
        remaining     = self._build_remaining(
            working,
            customer_ids, transaction_ids, account_ids,
            aml_patterns, countries,
        )

        result = EntityExtractionResult(
            customer_ids=customer_ids,
            transaction_ids=transaction_ids,
            account_ids=account_ids,
            risk_level=risk_level,
            aml_patterns=aml_patterns,
            countries=countries,
            amount_filters=amount_filters,
            date_filter=date_filter,
            limit=limit,
            raw_query=query,
            remaining_text=remaining,
        )

        logger.info(
            "Extraction complete — customers=%s txns=%s accounts=%s "
            "risk=%s patterns=%s countries=%s amounts=%d date=%s limit=%s",
            result.customer_ids, result.transaction_ids, result.account_ids,
            result.risk_level, result.aml_patterns, result.countries,
            len(result.amount_filters),
            result.date_filter.label if result.date_filter else None,
            result.limit,
        )
        return result

    # ------------------------------------------------------------------
    # Private extractors
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_customers(text: str) -> List[str]:
        return list(dict.fromkeys(m.group(1) for m in _RE_CUSTOMER.finditer(text)))

    @staticmethod
    def _extract_transactions(text: str) -> List[str]:
        return list(dict.fromkeys(m.group(1).upper() for m in _RE_TRANSACTION.finditer(text)))

    @staticmethod
    def _extract_accounts(text: str) -> List[str]:
        return list(dict.fromkeys(m.group(1) for m in _RE_ACCOUNT.finditer(text)))

    @staticmethod
    def _extract_risk_level(text: str) -> Optional[RiskLevelFilter]:
        m = _RE_RISK_LEVEL.search(text)
        if not m:
            return None
        key = m.group(1).lower().strip()
        return _RISK_LEVEL_MAP.get(key)

    @staticmethod
    def _extract_aml_patterns(text: str) -> List[str]:
        lower = text.lower()
        found: List[str] = []
        seen: Set[str] = set()
        for surface, canonical in _AML_PATTERNS_SORTED:
            if surface in lower and canonical not in seen:
                found.append(canonical)
                seen.add(canonical)
        return found

    @staticmethod
    def _extract_countries(text: str) -> List[str]:
        lower = text.lower()
        found: List[str] = []
        seen: Set[str] = set()
        for key, display in _COUNTRIES_SORTED:
            # Word-boundary-aware search
            if re.search(r"\b" + re.escape(key) + r"\b", lower):
                if display not in seen:
                    found.append(display)
                    seen.add(display)
        return found

    @staticmethod
    def _parse_amount(raw: str) -> float:
        """Expands shorthand (k/m/cr) and strips commas, returning a float."""
        raw = raw.strip().replace(",", "")

        def _expand(m: re.Match) -> str:
            num = float(m.group(1))
            suffix = m.group(2).lower()
            multiplier = {"k": 1_000, "m": 1_000_000, "cr": 10_000_000}[suffix]
            return str(num * multiplier)

        raw = _RE_SHORTHAND.sub(_expand, raw)
        return float(raw)

    @classmethod
    def _extract_amounts(cls, text: str) -> List[AmountFilter]:
        filters: List[AmountFilter] = []

        # BETWEEN takes priority — check first
        for m in _RE_AMOUNT_BETWEEN.finditer(text):
            lo = cls._parse_amount(m.group(1))
            hi = cls._parse_amount(m.group(2))
            filters.append(AmountFilter(operator=AmountOperator.BETWEEN, value=lo, upper=hi))

        # ABOVE
        for m in _RE_AMOUNT_ABOVE.finditer(text):
            # Skip if this span was already covered by BETWEEN
            if any(f.operator == AmountOperator.BETWEEN for f in filters):
                continue
            filters.append(AmountFilter(operator=AmountOperator.ABOVE, value=cls._parse_amount(m.group(1))))

        # BELOW
        for m in _RE_AMOUNT_BELOW.finditer(text):
            if any(f.operator == AmountOperator.BETWEEN for f in filters):
                continue
            filters.append(AmountFilter(operator=AmountOperator.BELOW, value=cls._parse_amount(m.group(1))))

        return filters

    @staticmethod
    def _extract_date(text: str) -> Optional[DateFilter]:
        for label, pattern, canonical in _DATE_PATTERNS:
            m = pattern.search(text)
            if not m:
                continue
            if canonical == "last_n_days":
                return DateFilter(label=f"last_{m.group(1)}_days")
            if canonical == "custom_range":
                return DateFilter(label="custom_range", start_date=m.group(1), end_date=m.group(2))
            return DateFilter(label=canonical)
        return None

    @staticmethod
    def _extract_limit(text: str) -> Optional[int]:
        m = _RE_LIMIT.search(text)
        return int(m.group(1)) if m else None

    @staticmethod
    def _build_remaining(
        text: str,
        customer_ids: List[str],
        transaction_ids: List[str],
        account_ids: List[str],
        aml_patterns: List[str],
        countries: List[str],
    ) -> str:
        """Returns the query with all extracted entity spans removed."""
        remaining = text
        for pat in (_RE_CUSTOMER, _RE_TRANSACTION, _RE_ACCOUNT,
                    _RE_RISK_LEVEL, _RE_LIMIT,
                    _RE_AMOUNT_BETWEEN, _RE_AMOUNT_ABOVE, _RE_AMOUNT_BELOW):
            remaining = pat.sub(" ", remaining)
        # Remove date filters
        for _, pattern, _ in _DATE_PATTERNS:
            remaining = pattern.sub(" ", remaining)
        # Remove AML surface forms
        lower = remaining.lower()
        for surface, _ in _AML_PATTERNS_SORTED:
            if surface in lower:
                remaining = re.sub(re.escape(surface), " ", remaining, flags=re.IGNORECASE)
                lower = remaining.lower()
        # Remove country names
        for key, _ in _COUNTRIES_SORTED:
            remaining = re.sub(r"\b" + re.escape(key) + r"\b", " ", remaining, flags=re.IGNORECASE)
        # Collapse whitespace
        return re.sub(r"\s+", " ", remaining).strip()
