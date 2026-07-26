# pyrefly: ignore [missing-import]
import pytest

from src.agent.entity_extractor import EntityExtractor
from src.agent.entity_models import (
    AmountFilter,
    AmountOperator,
    DateFilter,
    EntityExtractionResult,
    RiskLevelFilter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def extractor() -> EntityExtractor:
    return EntityExtractor()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract(extractor: EntityExtractor, query: str) -> EntityExtractionResult:
    return extractor.extract(query)


# ---------------------------------------------------------------------------
# Tests — Customer IDs
# ---------------------------------------------------------------------------

class TestCustomerExtraction:

    def test_numeric_customer_id(self, extractor):
        r = _extract(extractor, "Investigate customer 4521")
        assert "4521" in r.customer_ids

    def test_alphanumeric_customer_id(self, extractor):
        r = _extract(extractor, "Analyze customer C1001")
        assert "C1001" in r.customer_ids

    def test_multiple_customers(self, extractor):
        r = _extract(extractor, "Compare customer 1001 and customer 2002")
        assert "1001" in r.customer_ids
        assert "2002" in r.customer_ids

    def test_no_duplicate_customers(self, extractor):
        r = _extract(extractor, "customer 4521 and customer 4521")
        assert r.customer_ids.count("4521") == 1

    def test_no_customer_returns_empty(self, extractor):
        r = _extract(extractor, "Find structuring patterns")
        assert r.customer_ids == []

    def test_hyphenated_customer_id(self, extractor):
        r = _extract(extractor, "Review customer C-9900")
        assert "C-9900" in r.customer_ids


# ---------------------------------------------------------------------------
# Tests — Transaction IDs
# ---------------------------------------------------------------------------

class TestTransactionExtraction:

    def test_transaction_prefix(self, extractor):
        r = _extract(extractor, "Investigate transaction TX102")
        assert "TX102" in r.transaction_ids

    def test_txn_abbreviation(self, extractor):
        r = _extract(extractor, "Review txn 45001")
        assert "45001" in r.transaction_ids

    def test_tx_abbreviation(self, extractor):
        r = _extract(extractor, "Check tx 998")
        assert "998" in r.transaction_ids

    def test_transaction_ids_uppercased(self, extractor):
        r = _extract(extractor, "Investigate transaction tx102")
        assert "TX102" in r.transaction_ids

    def test_multiple_transactions(self, extractor):
        r = _extract(extractor, "Compare txn TX001 and txn TX002")
        assert "TX001" in r.transaction_ids
        assert "TX002" in r.transaction_ids

    def test_no_transaction_returns_empty(self, extractor):
        r = _extract(extractor, "Analyze high risk customers")
        assert r.transaction_ids == []


# ---------------------------------------------------------------------------
# Tests — Account IDs
# ---------------------------------------------------------------------------

class TestAccountExtraction:

    def test_account_prefix(self, extractor):
        r = _extract(extractor, "Investigate account A100")
        assert "A100" in r.account_ids

    def test_numeric_account_id(self, extractor):
        r = _extract(extractor, "Review account 12345")
        assert "12345" in r.account_ids

    def test_no_account_returns_empty(self, extractor):
        r = _extract(extractor, "Find smurfing patterns")
        assert r.account_ids == []


# ---------------------------------------------------------------------------
# Tests — Risk Levels
# ---------------------------------------------------------------------------

class TestRiskLevelExtraction:

    def test_high_risk(self, extractor):
        r = _extract(extractor, "Flag high risk customers")
        assert r.risk_level == RiskLevelFilter.HIGH

    def test_medium_risk(self, extractor):
        r = _extract(extractor, "List medium risk accounts")
        assert r.risk_level == RiskLevelFilter.MEDIUM

    def test_low_risk(self, extractor):
        r = _extract(extractor, "Show low risk transactions")
        assert r.risk_level == RiskLevelFilter.LOW

    def test_critical_risk(self, extractor):
        r = _extract(extractor, "Find critical risk customers")
        assert r.risk_level == RiskLevelFilter.CRITICAL

    def test_moderate_maps_to_medium(self, extractor):
        r = _extract(extractor, "Review moderate risk cases")
        assert r.risk_level == RiskLevelFilter.MEDIUM

    def test_no_risk_level_returns_none(self, extractor):
        r = _extract(extractor, "Find structuring patterns")
        assert r.risk_level is None


# ---------------------------------------------------------------------------
# Tests — AML Patterns
# ---------------------------------------------------------------------------

class TestAMLPatternExtraction:

    def test_structuring(self, extractor):
        r = _extract(extractor, "Find structuring patterns")
        assert "structuring" in r.aml_patterns

    def test_smurfing(self, extractor):
        r = _extract(extractor, "Detect smurfing activity")
        assert "smurfing" in r.aml_patterns

    def test_layering(self, extractor):
        r = _extract(extractor, "Identify layering schemes")
        assert "layering" in r.aml_patterns

    def test_money_mule(self, extractor):
        r = _extract(extractor, "Find money mule accounts")
        assert "money_mule" in r.aml_patterns

    def test_mule_shortform(self, extractor):
        r = _extract(extractor, "Detect mule transactions")
        assert "money_mule" in r.aml_patterns

    def test_circular_transactions(self, extractor):
        r = _extract(extractor, "Show circular transactions")
        assert "circular_transactions" in r.aml_patterns

    def test_round_tripping(self, extractor):
        r = _extract(extractor, "Check round tripping activity")
        assert "circular_transactions" in r.aml_patterns

    def test_rapid_fund_movement(self, extractor):
        r = _extract(extractor, "Detect rapid fund movement")
        assert "rapid_fund_movement" in r.aml_patterns

    def test_dormant_account(self, extractor):
        r = _extract(extractor, "Flag dormant account reactivations")
        assert "dormant_account" in r.aml_patterns

    def test_shell_company(self, extractor):
        r = _extract(extractor, "Investigate shell company transfers")
        assert "shell_company" in r.aml_patterns

    def test_multiple_patterns(self, extractor):
        r = _extract(extractor, "Find structuring and layering and smurfing")
        assert "structuring" in r.aml_patterns
        assert "layering" in r.aml_patterns
        assert "smurfing" in r.aml_patterns

    def test_no_pattern_returns_empty(self, extractor):
        r = _extract(extractor, "Investigate customer 4521")
        assert r.aml_patterns == []


# ---------------------------------------------------------------------------
# Tests — Countries
# ---------------------------------------------------------------------------

class TestCountryExtraction:

    def test_india(self, extractor):
        r = _extract(extractor, "Find transactions from India")
        assert "India" in r.countries

    def test_uae(self, extractor):
        r = _extract(extractor, "Transfers to UAE")
        assert "UAE" in r.countries

    def test_united_arab_emirates_normalised(self, extractor):
        r = _extract(extractor, "Transfers to United Arab Emirates")
        assert "UAE" in r.countries

    def test_singapore(self, extractor):
        r = _extract(extractor, "Find Singapore transfers")
        assert "Singapore" in r.countries

    def test_usa(self, extractor):
        r = _extract(extractor, "Transactions to USA")
        assert "USA" in r.countries

    def test_united_kingdom(self, extractor):
        r = _extract(extractor, "Investigate UK transfers")
        assert "United Kingdom" in r.countries

    def test_multiple_countries(self, extractor):
        r = _extract(extractor, "Transfers between India and UAE")
        assert "India" in r.countries
        assert "UAE" in r.countries

    def test_unknown_country_not_extracted(self, extractor):
        r = _extract(extractor, "Transfers from Atlantis")
        assert r.countries == []


# ---------------------------------------------------------------------------
# Tests — Amount Filters
# ---------------------------------------------------------------------------

class TestAmountExtraction:

    def test_above(self, extractor):
        r = _extract(extractor, "Transactions above 100000")
        assert len(r.amount_filters) == 1
        f = r.amount_filters[0]
        assert f.operator == AmountOperator.ABOVE
        assert f.value == 100000.0

    def test_greater_than(self, extractor):
        r = _extract(extractor, "Find transactions greater than 50000")
        f = r.amount_filters[0]
        assert f.operator == AmountOperator.ABOVE
        assert f.value == 50000.0

    def test_less_than(self, extractor):
        r = _extract(extractor, "Transactions less than 10000")
        f = r.amount_filters[0]
        assert f.operator == AmountOperator.BELOW
        assert f.value == 10000.0

    def test_below(self, extractor):
        r = _extract(extractor, "Amounts below 5000")
        f = r.amount_filters[0]
        assert f.operator == AmountOperator.BELOW

    def test_between(self, extractor):
        r = _extract(extractor, "Transactions between 10000 and 50000")
        f = r.amount_filters[0]
        assert f.operator == AmountOperator.BETWEEN
        assert f.value == 10000.0
        assert f.upper == 50000.0

    def test_k_shorthand(self, extractor):
        r = _extract(extractor, "Above 100k")
        assert r.amount_filters[0].value == 100_000.0

    def test_m_shorthand(self, extractor):
        r = _extract(extractor, "Greater than 1.5m")
        assert r.amount_filters[0].value == 1_500_000.0

    def test_no_amount_returns_empty(self, extractor):
        r = _extract(extractor, "Find structuring patterns")
        assert r.amount_filters == []


# ---------------------------------------------------------------------------
# Tests — Date Filters
# ---------------------------------------------------------------------------

class TestDateFilterExtraction:

    def test_today(self, extractor):
        r = _extract(extractor, "Show alerts from today")
        assert r.date_filter is not None
        assert r.date_filter.label == "today"

    def test_yesterday(self, extractor):
        r = _extract(extractor, "Transactions from yesterday")
        assert r.date_filter.label == "yesterday"

    def test_last_week(self, extractor):
        r = _extract(extractor, "Alerts from last week")
        assert r.date_filter.label == "last_week"

    def test_last_month(self, extractor):
        r = _extract(extractor, "Review last month transactions")
        assert r.date_filter.label == "last_month"

    def test_last_30_days(self, extractor):
        r = _extract(extractor, "Cases from last 30 days")
        assert r.date_filter.label == "last_30_days"

    def test_this_year(self, extractor):
        r = _extract(extractor, "Alerts for this year")
        assert r.date_filter.label == "this_year"

    def test_custom_range(self, extractor):
        r = _extract(extractor, "From 2024-01-01 to 2024-06-30")
        assert r.date_filter is not None
        assert r.date_filter.label == "custom_range"
        assert r.date_filter.start_date == "2024-01-01"
        assert r.date_filter.end_date == "2024-06-30"

    def test_no_date_returns_none(self, extractor):
        r = _extract(extractor, "Find high risk customers")
        assert r.date_filter is None


# ---------------------------------------------------------------------------
# Tests — Limit / Top-N
# ---------------------------------------------------------------------------

class TestLimitExtraction:

    def test_top_10(self, extractor):
        r = _extract(extractor, "Show top 10 suspicious customers")
        assert r.limit == 10

    def test_top_50(self, extractor):
        r = _extract(extractor, "Top 50 cases")
        assert r.limit == 50

    def test_no_limit_returns_none(self, extractor):
        r = _extract(extractor, "Find structuring patterns")
        assert r.limit is None


# ---------------------------------------------------------------------------
# Tests — Multiple Entities in One Query
# ---------------------------------------------------------------------------

class TestMultipleEntities:

    def test_combined_query(self, extractor):
        query = "Top 10 structuring cases for customer 4521 in India above 500000 last month"
        r = _extract(extractor, query)
        assert r.limit == 10
        assert "structuring" in r.aml_patterns
        assert "4521" in r.customer_ids
        assert "India" in r.countries
        assert any(f.operator == AmountOperator.ABOVE for f in r.amount_filters)
        assert r.date_filter is not None and r.date_filter.label == "last_month"

    def test_transaction_and_country(self, extractor):
        r = _extract(extractor, "Analyze transaction TX500 from Singapore")
        assert "TX500" in r.transaction_ids
        assert "Singapore" in r.countries


# ---------------------------------------------------------------------------
# Tests — Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_string_returns_empty_result(self, extractor):
        r = _extract(extractor, "")
        assert r.customer_ids == []
        assert r.transaction_ids == []
        assert r.aml_patterns == []
        assert r.risk_level is None
        assert r.limit is None

    def test_whitespace_only_returns_empty_result(self, extractor):
        r = _extract(extractor, "   ")
        assert r.customer_ids == []

    def test_gibberish_returns_empty_result(self, extractor):
        r = _extract(extractor, "asdf xyz qwerty")
        assert r.customer_ids == []
        assert r.aml_patterns == []
        assert r.countries == []

    def test_raw_query_preserved(self, extractor):
        q = "Investigate customer 4521"
        r = _extract(extractor, q)
        assert r.raw_query == q

    def test_result_is_dataclass(self, extractor):
        r = _extract(extractor, "Find structuring")
        assert isinstance(r, EntityExtractionResult)

    def test_remaining_text_extraction(self, extractor):
        r = _extract(extractor, "Please investigate customer C123 in India from last week above 50k")
        assert r.remaining_text.lower() == "please investigate in"

