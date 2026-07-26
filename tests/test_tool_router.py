# pyrefly: ignore [missing-import]
import pytest

from src.agent.plan_models import ExecutionPlan, LogicalTool, PlanStep
from src.agent.routing_models import StepStatus
from src.agent.tool_router import ToolRouter


@pytest.fixture
def router() -> ToolRouter:
    return ToolRouter()


def _mock_plan(steps: list[PlanStep]) -> ExecutionPlan:
    return ExecutionPlan(plan_id="test_plan", pattern_type="TEST", steps=steps)


class TestToolRouter:

    def test_linear_dependency(self, router):
        steps = [
            PlanStep("step1", "1", LogicalTool.LOAD_CUSTOMER),
            PlanStep("step2", "2", LogicalTool.RUN_RULE_ENGINE, dependencies=["step1"]),
            PlanStep("step3", "3", LogicalTool.RUN_RISK_FUSION, dependencies=["step2"])
        ]
        plan = _mock_plan(steps)
        routed = router.route(plan)
        
        assert len(routed.stages) == 3
        assert routed.stages[0].tools[0].step_id == "step1"
        assert routed.stages[1].tools[0].step_id == "step2"
        assert routed.stages[2].tools[0].step_id == "step3"

    def test_parallel_execution(self, router):
        steps = [
            PlanStep("load", "load", LogicalTool.LOAD_TRANSACTIONS),
            PlanStep("rule", "rule", LogicalTool.RUN_RULE_ENGINE, dependencies=["load"]),
            PlanStep("ml", "ml", LogicalTool.RUN_ML_ENGINE, dependencies=["load"]),
            PlanStep("fusion", "fusion", LogicalTool.RUN_RISK_FUSION, dependencies=["rule", "ml"])
        ]
        plan = _mock_plan(steps)
        routed = router.route(plan)
        
        assert len(routed.stages) == 3
        # Stage 1: load
        assert len(routed.stages[0].tools) == 1
        assert routed.stages[0].tools[0].step_id == "load"
        
        # Stage 2: rule and ml (parallel)
        assert len(routed.stages[1].tools) == 2
        stage_2_ids = {t.step_id for t in routed.stages[1].tools}
        assert "rule" in stage_2_ids
        assert "ml" in stage_2_ids
        
        # Stage 3: fusion
        assert len(routed.stages[2].tools) == 1
        assert routed.stages[2].tools[0].step_id == "fusion"

    def test_missing_input_blocks_step(self, router):
        steps = [
            PlanStep("load_cust", "load", LogicalTool.LOAD_CUSTOMER, required_inputs={"customer_ids": []}),
        ]
        plan = _mock_plan(steps)
        routed = router.route(plan)
        
        assert routed.stages[0].tools[0].status == StepStatus.BLOCKED

    def test_cyclic_dependency_raises_error(self, router):
        steps = [
            PlanStep("step1", "1", LogicalTool.LOAD_CUSTOMER, dependencies=["step2"]),
            PlanStep("step2", "2", LogicalTool.LOAD_TRANSACTIONS, dependencies=["step1"]),
        ]
        plan = _mock_plan(steps)
        
        with pytest.raises(ValueError, match="Cyclic dependency detected"):
            router.route(plan)

    def test_unknown_dependency_raises_error(self, router):
        steps = [
            PlanStep("step1", "1", LogicalTool.LOAD_CUSTOMER, dependencies=["ghost_step"]),
        ]
        plan = _mock_plan(steps)
        
        with pytest.raises(ValueError, match="UnknownDependencyError"):
            router.route(plan)

    def test_valid_numeric_input_not_blocked(self, router):
        steps = [
            PlanStep("step1", "1", LogicalTool.LOAD_CUSTOMER, required_inputs={"limit": 0, "flag": False}),
        ]
        plan = _mock_plan(steps)
        routed = router.route(plan)
        
        assert routed.stages[0].tools[0].status == StepStatus.READY
