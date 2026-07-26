# pyrefly: ignore [missing-import]
import pytest

from src.agent.context_memory import ContextMemoryManager, SessionNotFoundError
from src.agent.entity_models import EntityExtractionResult
from src.agent.intent_models import Intent, IntentResult
from src.agent.pattern_models import ConfidenceLevel, InvestigationPatternType, PatternIdentificationResult
from src.agent.plan_models import ExecutionPlan, LogicalTool, PlanStep
from src.agent.routing_models import RoutedPlan


@pytest.fixture
def manager() -> ContextMemoryManager:
    return ContextMemoryManager()


class TestContextMemoryManager:

    def test_create_session(self, manager):
        session_id = manager.create_session("INV-123")
        assert session_id is not None
        
        ctx = manager.get_session(session_id)
        assert ctx.session.session_id == session_id
        assert ctx.session.investigation_id == "INV-123"

    def test_invalid_session(self, manager):
        with pytest.raises(SessionNotFoundError):
            manager.get_session("nonexistent-id")
            
    def test_clear_session(self, manager):
        session_id = manager.create_session()
        manager.clear_session(session_id)
        
        with pytest.raises(SessionNotFoundError):
            manager.get_session(session_id)
            
    def test_clear_invalid_session(self, manager):
        with pytest.raises(SessionNotFoundError):
            manager.clear_session("nonexistent-id")

    def test_query_history(self, manager):
        session_id = manager.create_session()
        manager.update_query(session_id, "Find customer 123")
        manager.update_query(session_id, "What about their transactions?")
        
        ctx = manager.get_context(session_id)
        assert ctx.conversation_state.latest_query == "What about their transactions?"
        assert ctx.conversation_state.query_history == [
            "Find customer 123",
            "What about their transactions?"
        ]

    def test_store_intent(self, manager):
        session_id = manager.create_session()
        intent = IntentResult(Intent.CUSTOMER_INVESTIGATION, 1.0, [], "", "")
        
        manager.store_intent(session_id, intent)
        ctx = manager.get_context(session_id)
        
        assert ctx.planning_state.intent_result == intent

    def test_store_entities(self, manager):
        session_id = manager.create_session()
        entities = EntityExtractionResult(customer_ids=["123"])
        
        manager.store_entities(session_id, entities)
        ctx = manager.get_context(session_id)
        
        assert ctx.planning_state.entity_result == entities

    def test_store_pattern(self, manager):
        session_id = manager.create_session()
        pattern = PatternIdentificationResult(
            InvestigationPatternType.CUSTOMER_INVESTIGATION,
            0.95, ConfidenceLevel.HIGH, "test",
            IntentResult(Intent.CUSTOMER_INVESTIGATION, 1.0, [], "", ""),
            EntityExtractionResult()
        )
        
        manager.store_pattern(session_id, pattern)
        ctx = manager.get_context(session_id)
        
        assert ctx.planning_state.pattern_result == pattern

    def test_store_execution_plan(self, manager):
        session_id = manager.create_session()
        plan = ExecutionPlan("plan1", "TEST", [
            PlanStep("step1", "Desc", LogicalTool.LOAD_CUSTOMER),
            PlanStep("step2", "Desc", LogicalTool.RUN_RULE_ENGINE)
        ])
        
        manager.store_execution_plan(session_id, plan)
        ctx = manager.get_context(session_id)
        
        assert ctx.planning_state.execution_plan == plan
        # Verify pending steps are auto-populated
        assert ctx.execution_state.pending_steps == ["step1", "step2"]

    def test_store_routed_plan(self, manager):
        session_id = manager.create_session()
        routed_plan = RoutedPlan("plan1", [])
        
        manager.store_routed_plan(session_id, routed_plan)
        ctx = manager.get_context(session_id)
        
        assert ctx.planning_state.routed_plan == routed_plan

    def test_execution_tracking(self, manager):
        session_id = manager.create_session()
        plan = ExecutionPlan("plan1", "TEST", [
            PlanStep("step1", "Desc", LogicalTool.LOAD_CUSTOMER),
            PlanStep("step2", "Desc", LogicalTool.RUN_RULE_ENGINE),
            PlanStep("step3", "Desc", LogicalTool.RUN_ML_ENGINE)
        ])
        manager.store_execution_plan(session_id, plan)
        
        # Test stage update
        manager.set_current_stage(session_id, 1)
        assert manager.get_context(session_id).execution_state.current_stage == 1
        
        # Test completion
        manager.mark_step_completed(session_id, "step1")
        state = manager.get_context(session_id).execution_state
        assert "step1" in state.completed_steps
        assert "step1" not in state.pending_steps
        
        # Test failure
        manager.mark_step_failed(session_id, "step2")
        state = manager.get_context(session_id).execution_state
        assert "step2" in state.failed_steps
        assert "step2" not in state.pending_steps
        
        # Test recovering a failure
        manager.mark_step_completed(session_id, "step2")
        state = manager.get_context(session_id).execution_state
        assert "step2" in state.completed_steps
        assert "step2" not in state.failed_steps

    def test_mark_unknown_step_completed_raises(self, manager):
        session_id = manager.create_session()
        with pytest.raises(ValueError, match="Unknown step ID: unknown"):
            manager.mark_step_completed(session_id, "unknown")

    def test_mark_unknown_step_failed_raises(self, manager):
        session_id = manager.create_session()
        with pytest.raises(ValueError, match="Unknown step ID: unknown"):
            manager.mark_step_failed(session_id, "unknown")

    def test_duplicate_step_id_raises(self, manager):
        session_id = manager.create_session()
        plan = ExecutionPlan("plan1", "TEST", [
            PlanStep("step1", "Desc", LogicalTool.LOAD_CUSTOMER),
            PlanStep("step1", "Duplicate Desc", LogicalTool.LOAD_TRANSACTIONS)
        ])
        with pytest.raises(ValueError, match="Duplicate step ID"):
            manager.store_execution_plan(session_id, plan)

    def test_negative_stage_number_raises(self, manager):
        session_id = manager.create_session()
        with pytest.raises(ValueError, match="Stage number cannot be negative"):
            manager.set_current_stage(session_id, -1)

    def test_touch_updates_timestamp(self, manager):
        import time
        session_id = manager.create_session()
        ctx = manager.get_context(session_id)
        
        original_updated_at = ctx.session.updated_at
        time.sleep(0.01) # ensure a small delay
        
        manager.update_query(session_id, "test")
        assert ctx.session.updated_at > original_updated_at
