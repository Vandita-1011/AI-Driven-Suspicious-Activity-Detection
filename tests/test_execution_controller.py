# pyrefly: ignore [missing-import]
import pytest
from typing import Any, Dict

from src.agent.context_memory import ContextMemoryManager, SessionNotFoundError
from src.agent.execution_controller import ExecutionController, ToolExecutor
from src.agent.execution_models import ExecutionStatus
from src.agent.plan_models import LogicalTool, PlanStep
from src.agent.routing_models import ExecutionStage, RoutedPlan, RoutedStep, StepStatus


class DummyToolExecutor(ToolExecutor):
    """Mock tool executor used for test cases."""

    def __init__(self, return_val: Any = None):
        self.return_val = return_val or {"status": "success"}

    def execute_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Any:
        return self.return_val


class FailingToolExecutor(ToolExecutor):
    def __init__(self, fail_steps: list[str] = None):
        self.fail_steps = fail_steps or []
        self.attempts: Dict[str, int] = {}

    def execute_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Any:
        self.attempts[tool_name] = self.attempts.get(tool_name, 0) + 1
        if tool_name in self.fail_steps:
            raise RuntimeError(f"Tool {tool_name} failed intentionally.")
        return {"status": "success"}


class FlakyToolExecutor(ToolExecutor):
    def __init__(self, fail_times: int = 1):
        self.fail_times = fail_times
        self.attempts: Dict[str, int] = {}

    def execute_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Any:
        self.attempts[tool_name] = self.attempts.get(tool_name, 0) + 1
        if self.attempts[tool_name] <= self.fail_times:
            raise RuntimeError(f"Flaky failure #{self.attempts[tool_name]}")
        return {"status": "success"}


@pytest.fixture
def memory_manager() -> ContextMemoryManager:
    return ContextMemoryManager()


@pytest.fixture
def dummy_executor() -> DummyToolExecutor:
    return DummyToolExecutor()


def _create_sample_routed_plan(plan_id: str = "p1") -> RoutedPlan:
    step1 = PlanStep("s1", "Step 1", LogicalTool.LOAD_CUSTOMER, required_inputs={"cust_id": "123"})
    step2 = PlanStep("s2", "Step 2", LogicalTool.RUN_RULE_ENGINE, required_inputs={"cust_id": "123"})
    routed1 = RoutedStep(step1, status=StepStatus.READY)
    routed2 = RoutedStep(step2, status=StepStatus.READY)

    stage1 = ExecutionStage(1, [routed1])
    stage2 = ExecutionStage(2, [routed2])

    return RoutedPlan(plan_id=plan_id, stages=[stage1, stage2])


class TestExecutionController:

    def test_successful_execution(self, memory_manager, dummy_executor):
        session_id = memory_manager.create_session()
        routed_plan = _create_sample_routed_plan()

        controller = ExecutionController(memory_manager, dummy_executor)
        result = controller.execute(session_id, routed_plan)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.completed_steps == ["s1", "s2"]
        assert not result.failed_steps
        assert len(result.execution_log) == 2

        # Context Memory check
        ctx = memory_manager.get_session(session_id)
        assert ctx.execution_state.completed_steps == ["s1", "s2"]
        assert ctx.execution_state.current_stage == 2

    def test_missing_session_raises_error(self, memory_manager, dummy_executor):
        routed_plan = _create_sample_routed_plan()
        controller = ExecutionController(memory_manager, dummy_executor)

        with pytest.raises(SessionNotFoundError):
            controller.execute("invalid-session-id", routed_plan)

    def test_empty_routed_plan_raises_error(self, memory_manager, dummy_executor):
        session_id = memory_manager.create_session()
        empty_plan = RoutedPlan("p_empty", stages=[])
        controller = ExecutionController(memory_manager, dummy_executor)

        with pytest.raises(ValueError, match="Routed plan is empty"):
            controller.execute(session_id, empty_plan)

    def test_missing_inputs_raises_error(self, memory_manager, dummy_executor):
        session_id = memory_manager.create_session()
        step = PlanStep("s_bad", "Bad Step", LogicalTool.LOAD_CUSTOMER, required_inputs={"cust_id": None})
        routed_step = RoutedStep(step, status=StepStatus.BLOCKED)
        plan = RoutedPlan("p_bad", stages=[ExecutionStage(1, [routed_step])])

        controller = ExecutionController(memory_manager, dummy_executor)
        with pytest.raises(ValueError, match="Missing required execution inputs"):
            controller.execute(session_id, plan)

    def test_failed_execution_and_attempt_logging(self, memory_manager):
        session_id = memory_manager.create_session()
        routed_plan = _create_sample_routed_plan()

        executor = FailingToolExecutor(fail_steps=[LogicalTool.RUN_RULE_ENGINE.value])
        controller = ExecutionController(memory_manager, tool_executor=executor, max_retries=2)

        result = controller.execute(session_id, routed_plan)

        assert result.status == ExecutionStatus.PARTIAL_SUCCESS
        assert result.completed_steps == ["s1"]
        assert result.failed_steps == ["s2"]
        assert len(result.errors) == 1
        assert executor.attempts[LogicalTool.RUN_RULE_ENGINE.value] == 3  # 1 initial + 2 retries

        # Check attempt logs: 1 for s1 success, 3 for s2 failed attempts
        s2_logs = [log for log in result.execution_log if log.step_id == "s2"]
        assert len(s2_logs) == 3

    def test_complete_failure(self, memory_manager):
        session_id = memory_manager.create_session()
        step1 = PlanStep("s1", "Step 1", LogicalTool.LOAD_CUSTOMER, required_inputs={"cust_id": "123"})
        plan = RoutedPlan("p_fail", stages=[ExecutionStage(1, [RoutedStep(step1, status=StepStatus.READY)])])

        executor = FailingToolExecutor(fail_steps=[LogicalTool.LOAD_CUSTOMER.value])
        controller = ExecutionController(memory_manager, tool_executor=executor, max_retries=1)

        result = controller.execute(session_id, plan)

        assert result.status == ExecutionStatus.FAILED
        assert result.failed_steps == ["s1"]
        assert not result.completed_steps

    def test_flaky_tool_retry_success(self, memory_manager):
        session_id = memory_manager.create_session()
        step1 = PlanStep("s1", "Flaky Step", LogicalTool.RUN_RULE_ENGINE, required_inputs={"k": "v"})
        plan = RoutedPlan("p_flaky", stages=[ExecutionStage(1, [RoutedStep(step1, status=StepStatus.READY)])])

        executor = FlakyToolExecutor(fail_times=1)
        controller = ExecutionController(memory_manager, tool_executor=executor, max_retries=2)

        result = controller.execute(session_id, plan)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.completed_steps == ["s1"]
        assert executor.attempts[LogicalTool.RUN_RULE_ENGINE.value] == 2

    def test_cancel_execution(self, memory_manager, dummy_executor):
        session_id = memory_manager.create_session()
        routed_plan = _create_sample_routed_plan()

        controller = ExecutionController(memory_manager, dummy_executor)
        res_dummy = controller.execute(session_id, routed_plan)
        controller.cancel_execution(res_dummy.execution_id)

        assert controller.get_execution_status(res_dummy.execution_id) == ExecutionStatus.CANCELLED

    def test_retry_on_completed_execution_does_not_mutate(self, memory_manager, dummy_executor):
        session_id = memory_manager.create_session()
        routed_plan = _create_sample_routed_plan()

        controller = ExecutionController(memory_manager, dummy_executor)
        result = controller.execute(session_id, routed_plan)
        assert result.status == ExecutionStatus.COMPLETED

        retried_result = controller.retry_failed_steps(result.execution_id)
        assert retried_result.status == ExecutionStatus.COMPLETED
