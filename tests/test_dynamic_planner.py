# pyrefly: ignore [missing-import]
import pytest

from src.agent.intent_models import Intent, IntentResult
from src.agent.entity_models import EntityExtractionResult
from src.agent.pattern_models import ConfidenceLevel, InvestigationPatternType, PatternIdentificationResult
from src.agent.plan_models import LogicalTool
from src.agent.dynamic_planner import DynamicPlanner


@pytest.fixture
def planner() -> DynamicPlanner:
    return DynamicPlanner()


def _mock_pattern_result(
    pattern: InvestigationPatternType = InvestigationPatternType.CUSTOMER_INVESTIGATION,
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH,
    entities: EntityExtractionResult = None
) -> PatternIdentificationResult:
    if entities is None:
        entities = EntityExtractionResult(customer_ids=["1234"])
    return PatternIdentificationResult(
        investigation_pattern=pattern,
        confidence_score=0.95,
        confidence_level=confidence_level,
        reasoning="Test",
        matched_intent=IntentResult(Intent.CUSTOMER_INVESTIGATION, 1.0, [], "", ""),
        matched_entities=entities
    )


class TestDynamicPlanner:

    def test_generate_plan_customer_investigation(self, planner):
        result = _mock_pattern_result(
            InvestigationPatternType.CUSTOMER_INVESTIGATION,
            ConfidenceLevel.HIGH,
            EntityExtractionResult(customer_ids=["999"])
        )
        plan = planner.generate_plan(result)
        
        assert plan.pattern_type == InvestigationPatternType.CUSTOMER_INVESTIGATION.value
        assert len(plan.steps) > 5
        
        # Verify inputs injected
        load_cust_step = next(s for s in plan.steps if s.step_id == "load_cust")
        assert load_cust_step.required_inputs["customer_ids"] == ["999"]
        
        # Ensure no manual review
        assert not any(s.logical_tool == LogicalTool.MANUAL_REVIEW for s in plan.steps)

    def test_low_confidence_inserts_manual_review(self, planner):
        result = _mock_pattern_result(
            InvestigationPatternType.CUSTOMER_INVESTIGATION,
            ConfidenceLevel.LOW,
            EntityExtractionResult(customer_ids=["999"])
        )
        plan = planner.generate_plan(result)
        
        # First step should be manual review
        assert plan.steps[0].step_id == "manual_review"
        assert plan.steps[0].logical_tool == LogicalTool.MANUAL_REVIEW
        
        # Load steps should now depend on manual review
        load_cust_step = next(s for s in plan.steps if s.step_id == "load_cust")
        assert "manual_review" in load_cust_step.dependencies

    def test_unsupported_pattern_raises_error(self, planner):
        result = _mock_pattern_result(InvestigationPatternType.CUSTOM_INVESTIGATION)
        with pytest.raises(NotImplementedError, match="No plan template defined"):
            planner.generate_plan(result)

    def test_metadata_enrichment(self, planner):
        result = _mock_pattern_result(
            InvestigationPatternType.CUSTOMER_INVESTIGATION,
            ConfidenceLevel.HIGH
        )
        plan = planner.generate_plan(result)
        
        assert plan.metadata["investigation_pattern"] == InvestigationPatternType.CUSTOMER_INVESTIGATION.value
        assert plan.metadata["confidence_score"] == 0.95
        assert plan.metadata["confidence_level"] == ConfidenceLevel.HIGH.value
        assert plan.metadata["reasoning"] == "Test"
