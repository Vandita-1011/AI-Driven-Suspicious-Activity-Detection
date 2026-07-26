# pyrefly: ignore [missing-import]
import pytest

from src.agent.intent_models import Intent, IntentResult
from src.agent.entity_models import EntityExtractionResult
from src.agent.pattern_models import ConfidenceLevel, InvestigationPatternType
from src.agent.pattern_identifier import PatternIdentifier


@pytest.fixture
def identifier() -> PatternIdentifier:
    return PatternIdentifier()


def _mock_intent(intent: Intent, confidence: float = 1.0, raw: str = "") -> IntentResult:
    return IntentResult(
        intent=intent,
        confidence=confidence,
        matched_phrases=[],
        raw_query=raw,
        normalized_query=""
    )


class TestPatternIdentifier:

    def test_customer_investigation_success(self, identifier):
        intent = _mock_intent(Intent.CUSTOMER_INVESTIGATION)
        entities = EntityExtractionResult(customer_ids=["1234"])
        
        result = identifier.identify(intent, entities)
        
        assert result.investigation_pattern == InvestigationPatternType.CUSTOMER_INVESTIGATION
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert not result.missing_entities

    def test_customer_investigation_missing_entity(self, identifier):
        intent = _mock_intent(Intent.CUSTOMER_INVESTIGATION, confidence=0.8)
        entities = EntityExtractionResult(customer_ids=[]) # Missing customer ID
        
        result = identifier.identify(intent, entities)
        
        assert "customer_ids" in result.missing_entities
        assert result.confidence_score == 0.5  # 0.8 - 0.30 penalty
        assert result.confidence_level == ConfidenceLevel.LOW
        assert "Missing required entities: customer_ids" in result.validation_messages

    def test_transaction_investigation_success(self, identifier):
        intent = _mock_intent(Intent.TRANSACTION_INVESTIGATION)
        entities = EntityExtractionResult(transaction_ids=["TX999"])
        
        result = identifier.identify(intent, entities)
        
        assert result.investigation_pattern == InvestigationPatternType.TRANSACTION_INVESTIGATION
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert not result.missing_entities

    def test_structuring_investigation(self, identifier):
        intent = _mock_intent(Intent.AML_PATTERN_SEARCH)
        entities = EntityExtractionResult(aml_patterns=["structuring"])
        
        result = identifier.identify(intent, entities)
        
        assert result.investigation_pattern == InvestigationPatternType.STRUCTURING_INVESTIGATION
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert not result.missing_entities

    def test_top_n_investigation(self, identifier):
        intent = _mock_intent(Intent.DATASET_ANALYSIS)
        entities = EntityExtractionResult(limit=10)
        
        result = identifier.identify(intent, entities)
        
        assert result.investigation_pattern == InvestigationPatternType.TOP_N_INVESTIGATION
        assert result.confidence_level == ConfidenceLevel.HIGH

    def test_country_risk_investigation(self, identifier):
        intent = _mock_intent(Intent.DATASET_ANALYSIS)
        entities = EntityExtractionResult(countries=["India"])
        
        result = identifier.identify(intent, entities)
        
        assert result.investigation_pattern == InvestigationPatternType.COUNTRY_RISK_INVESTIGATION

    def test_fallback_custom_investigation(self, identifier):
        intent = _mock_intent(Intent.UNKNOWN)
        entities = EntityExtractionResult()
        
        result = identifier.identify(intent, entities)
        
        assert result.investigation_pattern == InvestigationPatternType.CUSTOM_INVESTIGATION
