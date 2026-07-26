# pyrefly: ignore [missing-import]
import pytest

from src.agent.intent_models import Intent, IntentResult
from src.agent.intent_recognizer import IntentRecognizer
from src.agent.intent_catalog import MAX_SCORE_PER_INTENT


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def recognizer() -> IntentRecognizer:
    return IntentRecognizer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_intent(recognizer: IntentRecognizer, query: str, expected: Intent) -> IntentResult:
    result = recognizer.recognize(query)
    assert result.intent == expected, (
        f"Query '{query}' → expected {expected.value}, got {result.intent.value} "
        f"(confidence={result.confidence:.3f}, phrases={result.matched_phrases})"
    )
    return result


# ---------------------------------------------------------------------------
# Tests — DATASET_ANALYSIS
# ---------------------------------------------------------------------------

class TestDatasetAnalysis:

    def test_canonical_query(self, recognizer):
        _assert_intent(recognizer, "Analyze this dataset for suspicious activity", Intent.DATASET_ANALYSIS)

    def test_british_spelling(self, recognizer):
        _assert_intent(recognizer, "Analyse dataset for suspicious activity", Intent.DATASET_ANALYSIS)

    def test_run_pipeline_variation(self, recognizer):
        _assert_intent(recognizer, "Run the pipeline", Intent.DATASET_ANALYSIS)

    def test_full_detection_variation(self, recognizer):
        _assert_intent(recognizer, "Start full detection", Intent.DATASET_ANALYSIS)

    def test_scan_dataset(self, recognizer):
        _assert_intent(recognizer, "Scan dataset for issues", Intent.DATASET_ANALYSIS)

    def test_detect_suspicious(self, recognizer):
        _assert_intent(recognizer, "Detect suspicious transactions", Intent.DATASET_ANALYSIS)


# ---------------------------------------------------------------------------
# Tests — AML_PATTERN_SEARCH
# ---------------------------------------------------------------------------

class TestAMLPatternSearch:

    def test_canonical_query(self, recognizer):
        _assert_intent(recognizer, "Find structuring patterns", Intent.AML_PATTERN_SEARCH)

    def test_detect_aml_patterns(self, recognizer):
        _assert_intent(recognizer, "Detect AML patterns in the dataset", Intent.AML_PATTERN_SEARCH)

    def test_money_laundering_pattern(self, recognizer):
        _assert_intent(recognizer, "Look for money laundering patterns", Intent.AML_PATTERN_SEARCH)

    def test_structuring_only(self, recognizer):
        _assert_intent(recognizer, "Show me structuring", Intent.AML_PATTERN_SEARCH)

    def test_smurfing(self, recognizer):
        _assert_intent(recognizer, "Identify smurfing activity", Intent.AML_PATTERN_SEARCH)

    def test_layering(self, recognizer):
        _assert_intent(recognizer, "Detect layering schemes", Intent.AML_PATTERN_SEARCH)

    def test_typology(self, recognizer):
        _assert_intent(recognizer, "Show typology matches", Intent.AML_PATTERN_SEARCH)

    def test_mule_accounts(self, recognizer):
        _assert_intent(recognizer, "Find mule accounts", Intent.AML_PATTERN_SEARCH)


# ---------------------------------------------------------------------------
# Tests — HIGH_RISK_CUSTOMER
# ---------------------------------------------------------------------------

class TestHighRiskCustomer:

    def test_canonical_query(self, recognizer):
        _assert_intent(recognizer, "Flag high risk customers", Intent.HIGH_RISK_CUSTOMER)

    def test_high_risk_account(self, recognizer):
        _assert_intent(recognizer, "Show me high risk accounts", Intent.HIGH_RISK_CUSTOMER)

    def test_critical_risk_customer(self, recognizer):
        _assert_intent(recognizer, "Find critical risk customer", Intent.HIGH_RISK_CUSTOMER)

    def test_suspicious_customer(self, recognizer):
        _assert_intent(recognizer, "List suspicious customers", Intent.HIGH_RISK_CUSTOMER)

    def test_flag_customer(self, recognizer):
        _assert_intent(recognizer, "Flag this customer for review", Intent.HIGH_RISK_CUSTOMER)


# ---------------------------------------------------------------------------
# Tests — CUSTOMER_INVESTIGATION
# ---------------------------------------------------------------------------

class TestCustomerInvestigation:

    def test_canonical_query(self, recognizer):
        _assert_intent(recognizer, "Investigate customer 4521", Intent.CUSTOMER_INVESTIGATION)

    def test_look_into_customer(self, recognizer):
        _assert_intent(recognizer, "Look into customer account", Intent.CUSTOMER_INVESTIGATION)

    def test_analyze_customer(self, recognizer):
        _assert_intent(recognizer, "Analyze customer profile", Intent.CUSTOMER_INVESTIGATION)

    def test_review_customer(self, recognizer):
        _assert_intent(recognizer, "Review customer history", Intent.CUSTOMER_INVESTIGATION)

    def test_customer_investigation_phrase(self, recognizer):
        _assert_intent(recognizer, "Customer investigation required", Intent.CUSTOMER_INVESTIGATION)


# ---------------------------------------------------------------------------
# Tests — TRANSACTION_INVESTIGATION
# ---------------------------------------------------------------------------

class TestTransactionInvestigation:

    def test_canonical_query(self, recognizer):
        _assert_intent(recognizer, "Investigate transaction TX102", Intent.TRANSACTION_INVESTIGATION)

    def test_look_into_transaction(self, recognizer):
        _assert_intent(recognizer, "Look into this transaction", Intent.TRANSACTION_INVESTIGATION)

    def test_analyze_transaction(self, recognizer):
        _assert_intent(recognizer, "Analyze transaction details", Intent.TRANSACTION_INVESTIGATION)

    def test_check_transaction(self, recognizer):
        _assert_intent(recognizer, "Check transaction TX999", Intent.TRANSACTION_INVESTIGATION)

    def test_txn_abbreviation(self, recognizer):
        _assert_intent(recognizer, "Review txn 00123", Intent.TRANSACTION_INVESTIGATION)

    def test_tx_abbreviation(self, recognizer):
        _assert_intent(recognizer, "What happened with tx 99?", Intent.TRANSACTION_INVESTIGATION)


# ---------------------------------------------------------------------------
# Tests — DASHBOARD_SUMMARY
# ---------------------------------------------------------------------------

class TestDashboardSummary:

    def test_canonical_query(self, recognizer):
        _assert_intent(recognizer, "Generate dashboard summary", Intent.DASHBOARD_SUMMARY)

    def test_executive_summary(self, recognizer):
        _assert_intent(recognizer, "Show executive summary", Intent.DASHBOARD_SUMMARY)

    def test_show_dashboard(self, recognizer):
        _assert_intent(recognizer, "Show me the dashboard", Intent.DASHBOARD_SUMMARY)

    def test_overall_summary(self, recognizer):
        _assert_intent(recognizer, "Give overall summary", Intent.DASHBOARD_SUMMARY)

    def test_dashboard_overview(self, recognizer):
        _assert_intent(recognizer, "Dashboard overview", Intent.DASHBOARD_SUMMARY)


# ---------------------------------------------------------------------------
# Tests — REPORT_GENERATION
# ---------------------------------------------------------------------------

class TestReportGeneration:

    def test_canonical_query(self, recognizer):
        _assert_intent(recognizer, "Generate investigation report", Intent.REPORT_GENERATION)

    def test_create_report(self, recognizer):
        _assert_intent(recognizer, "Create a report", Intent.REPORT_GENERATION)

    def test_produce_report(self, recognizer):
        _assert_intent(recognizer, "Produce the report", Intent.REPORT_GENERATION)

    def test_export_report(self, recognizer):
        _assert_intent(recognizer, "Export report to PDF", Intent.REPORT_GENERATION)

    def test_sar_report(self, recognizer):
        _assert_intent(recognizer, "File SAR report", Intent.REPORT_GENERATION)

    def test_investigation_report(self, recognizer):
        _assert_intent(recognizer, "Investigation report needed", Intent.REPORT_GENERATION)


# ---------------------------------------------------------------------------
# Tests — UNKNOWN
# ---------------------------------------------------------------------------

class TestUnknown:

    def test_empty_string(self, recognizer):
        result = recognizer.recognize("")
        assert result.intent == Intent.UNKNOWN
        assert result.confidence == 0.0

    def test_whitespace_only(self, recognizer):
        result = recognizer.recognize("   ")
        assert result.intent == Intent.UNKNOWN

    def test_gibberish(self, recognizer):
        result = recognizer.recognize("asdfqwer xyz abc")
        assert result.intent == Intent.UNKNOWN

    def test_unrelated_topic(self, recognizer):
        result = recognizer.recognize("Order more printer paper")
        assert result.intent == Intent.UNKNOWN


# ---------------------------------------------------------------------------
# Tests — IntentResult structure
# ---------------------------------------------------------------------------

class TestIntentResult:

    def test_result_is_dataclass(self, recognizer):
        result = recognizer.recognize("Find structuring patterns")
        assert isinstance(result, IntentResult)

    def test_confidence_in_range(self, recognizer):
        result = recognizer.recognize("Investigate customer 4521")
        assert 0.0 <= result.confidence <= 1.0

    def test_raw_query_preserved(self, recognizer):
        q = "Investigate customer 4521"
        result = recognizer.recognize(q)
        assert result.raw_query == q

    def test_normalized_query_lowercase(self, recognizer):
        result = recognizer.recognize("INVESTIGATE CUSTOMER 4521!")
        assert result.normalized_query == result.normalized_query.lower()
        assert "!" not in result.normalized_query

    def test_matched_phrases_populated_on_hit(self, recognizer):
        result = recognizer.recognize("Find structuring patterns")
        assert len(result.matched_phrases) > 0

    def test_matched_phrases_empty_on_unknown(self, recognizer):
        result = recognizer.recognize("")
        assert result.matched_phrases == []

    def test_high_confidence_for_specific_phrase(self, recognizer):
        # Highly specific 3-token phrase should yield a meaningful confidence
        result = recognizer.recognize("Analyze dataset for suspicious activity detection")
        assert result.confidence >= 0.10

    def test_supported_intents_excludes_unknown(self, recognizer):
        supported = recognizer.supported_intents()
        assert Intent.UNKNOWN not in supported
        assert Intent.DATASET_ANALYSIS in supported
        assert len(supported) == 7

    def test_punctuation_stripped(self, recognizer):
        result = recognizer.recognize("Investigate! customer... 4521?")
        assert result.intent == Intent.CUSTOMER_INVESTIGATION

    def test_case_insensitive(self, recognizer):
        result = recognizer.recognize("FIND STRUCTURING PATTERNS")
        assert result.intent == Intent.AML_PATTERN_SEARCH


# ---------------------------------------------------------------------------
# Tests — Per-intent confidence normalisation
# ---------------------------------------------------------------------------

class TestPerIntentConfidence:

    def test_confident_specific_query_scores_high(self, recognizer):
        # A query that matches the most-specific 3-token rule for DATASET_ANALYSIS
        # should yield a meaningful confidence even though DATASET_ANALYSIS has
        # many catalogue entries, because we normalise per intent.
        result = recognizer.recognize("Analyze dataset for suspicious activity")
        assert result.intent == Intent.DATASET_ANALYSIS
        assert result.confidence >= 0.15, (
            f"Expected per-intent confidence >= 0.15, got {result.confidence:.4f}"
        )

    def test_single_keyword_yields_lower_confidence_than_phrase(self, recognizer):
        # "structuring" alone (weight 1.5) should score lower than
        # "find structuring pattern" (weight 3.0 + possible 2.5).
        single = recognizer.recognize("Show structuring")
        specific = recognizer.recognize("Find structuring patterns")
        assert single.intent == Intent.AML_PATTERN_SEARCH
        assert specific.intent == Intent.AML_PATTERN_SEARCH
        assert specific.confidence > single.confidence, (
            f"Specific phrase ({specific.confidence:.4f}) should outscore "
            f"single keyword ({single.confidence:.4f})"
        )

    def test_per_intent_max_score_is_positive(self):
        for intent, max_score in MAX_SCORE_PER_INTENT.items():
            assert max_score > 0.0, f"Max score for {intent.value} must be positive"
