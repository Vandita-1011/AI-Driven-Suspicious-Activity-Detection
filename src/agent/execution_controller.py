"""
Execution Controller
====================
Orchestrates sequential execution of a RoutedPlan, updates Context Memory,
handles retries and failure policies, and maintains execution logs.
"""
from __future__ import annotations

import datetime
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.agent.context_memory import ContextMemoryManager, SessionNotFoundError
from src.agent.execution_models import (
    ExecutionLogEntry,
    ExecutionResult,
    ExecutionStatus,
)
from src.agent.routing_models import RoutedPlan, RoutedStep, StepStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ToolExecutor(ABC):
    """
    Abstract interface for executing logical tools.
    Decouples the ExecutionController from physical engine implementations.
    """

    @abstractmethod
    def execute_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Any:
        """Executes a tool by name with provided inputs."""
        pass


class ExecutionController:
    """
    Orchestrates execution of routed plans deterministically and sequentially.
    """

    def __init__(
        self,
        memory_manager: ContextMemoryManager,
        tool_executor: ToolExecutor,
        max_retries: int = 2,
    ) -> None:
        self.memory_manager = memory_manager
        self.tool_executor = tool_executor
        self.max_retries = max_retries

        # Execution tracking
        self._executions: Dict[str, ExecutionResult] = {}
        self._cancelled_executions: set[str] = set()
        self._execution_plans: Dict[str, RoutedPlan] = {}

    def execute(self, session_id: str, routed_plan: RoutedPlan) -> ExecutionResult:
        """
        Executes a RoutedPlan stage-by-stage sequentially.
        """
        # 1. Validate Session Prerequisite
        ctx = self.memory_manager.get_session(session_id)

        # 2. Validate Plan Prerequisite
        if not routed_plan or not routed_plan.stages:
            raise ValueError("Routed plan is empty.")

        for stage in routed_plan.stages:
            for step in stage.tools:
                if step.status == StepStatus.BLOCKED:
                    raise ValueError(
                        f"Missing required execution inputs for step '{step.step_id}'."
                    )

        # 3. Initialize Execution
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        started_at = datetime.datetime.utcnow()

        result = ExecutionResult(
            execution_id=execution_id,
            session_id=session_id,
            plan_id=routed_plan.plan_id,
            status=ExecutionStatus.RUNNING,
            started_at=started_at,
            completed_steps=[],
            failed_steps=[],
            execution_log=[],
            errors=[],
        )
        self._executions[execution_id] = result
        self._execution_plans[execution_id] = routed_plan

        # Store routed plan in context memory
        self.memory_manager.store_routed_plan(session_id, routed_plan)

        logger.info(
            "Starting execution %s for session %s (plan %s)",
            execution_id,
            session_id,
            routed_plan.plan_id,
        )

        # 4. Execute Stages Sequentially
        cancelled = False

        for stage in routed_plan.stages:
            if execution_id in self._cancelled_executions:
                cancelled = True
                break

            self.memory_manager.set_current_stage(session_id, stage.stage_number)
            logger.info("Executing stage %d", stage.stage_number)

            for step in stage.tools:
                if execution_id in self._cancelled_executions:
                    cancelled = True
                    break

                self._execute_single_step(session_id, result, step)

            if cancelled:
                break

        # 5. Finalize Result
        result.finished_at = datetime.datetime.utcnow()

        if cancelled or execution_id in self._cancelled_executions:
            result.status = ExecutionStatus.CANCELLED
            self._add_log(
                result,
                step_id="SYSTEM",
                tool_name="SYSTEM",
                status=ExecutionStatus.CANCELLED,
                message="Execution was cancelled.",
            )
        elif not result.failed_steps:
            result.status = ExecutionStatus.COMPLETED
        elif result.completed_steps and result.failed_steps:
            result.status = ExecutionStatus.PARTIAL_SUCCESS
        else:
            result.status = ExecutionStatus.FAILED

        logger.info(
            "Finished execution %s with status %s", execution_id, result.status.value
        )
        return result

    def cancel_execution(self, execution_id: str) -> None:
        """Cancels an ongoing execution."""
        if execution_id not in self._executions:
            raise ValueError(f"Execution ID {execution_id} not found.")

        self._cancelled_executions.add(execution_id)
        result = self._executions[execution_id]
        if result.status == ExecutionStatus.RUNNING:
            result.status = ExecutionStatus.CANCELLED
            result.finished_at = datetime.datetime.utcnow()
        logger.info("Cancelled execution: %s", execution_id)

    def get_execution_status(self, execution_id: str) -> ExecutionStatus:
        """Gets status of an execution."""
        if execution_id not in self._executions:
            raise ValueError(f"Execution ID {execution_id} not found.")
        return self._executions[execution_id].status

    def get_execution_result(self, execution_id: str) -> ExecutionResult:
        """Gets full execution result."""
        if execution_id not in self._executions:
            raise ValueError(f"Execution ID {execution_id} not found.")
        return self._executions[execution_id]

    def retry_failed_steps(self, execution_id: str) -> ExecutionResult:
        """Retries ONLY failed steps from a previous execution run without modifying completed/cancelled executions."""
        if execution_id not in self._executions:
            raise ValueError(f"Execution ID {execution_id} not found.")

        result = self._executions[execution_id]
        routed_plan = self._execution_plans[execution_id]
        session_id = result.session_id

        # Do not modify completed or cancelled executions
        if result.status in (ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED):
            logger.info(
                "Execution %s is %s. Skipping retry.", execution_id, result.status.value
            )
            return result

        if result.status not in (ExecutionStatus.FAILED, ExecutionStatus.PARTIAL_SUCCESS):
            return result

        logger.info("Retrying failed steps for execution %s", execution_id)
        result.status = ExecutionStatus.RUNNING

        failed_step_ids = list(result.failed_steps)
        result.failed_steps.clear()

        for stage in routed_plan.stages:
            for step in stage.tools:
                if step.step_id in failed_step_ids:
                    self._execute_single_step(session_id, result, step)

        result.finished_at = datetime.datetime.utcnow()

        if not result.failed_steps:
            result.status = ExecutionStatus.COMPLETED
        elif result.completed_steps and result.failed_steps:
            result.status = ExecutionStatus.PARTIAL_SUCCESS
        else:
            result.status = ExecutionStatus.FAILED

        return result

    def _execute_single_step(
        self, session_id: str, result: ExecutionResult, step: RoutedStep
    ) -> None:
        """Executes a single step with retries and detailed logging for every attempt."""
        step_id = step.step_id
        tool_name = step.plan_step.logical_tool.value
        inputs = step.plan_step.required_inputs

        attempts = 0
        success = False
        last_error = ""
        total_attempts = 1 + self.max_retries

        while attempts < total_attempts and not success:
            attempts += 1
            try:
                logger.debug("Executing step %s (Attempt %d)", step_id, attempts)
                self.tool_executor.execute_tool(tool_name, inputs)
                success = True
                self._add_log(
                    result,
                    step_id=step_id,
                    tool_name=tool_name,
                    status=ExecutionStatus.COMPLETED,
                    message=f"Attempt {attempts}/{total_attempts}: Executed successfully.",
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Step %s failed attempt %d: %s", step_id, attempts, last_error
                )
                self._add_log(
                    result,
                    step_id=step_id,
                    tool_name=tool_name,
                    status=ExecutionStatus.FAILED,
                    message=f"Attempt {attempts}/{total_attempts} failed: {last_error}",
                )

        if success:
            if step_id not in result.completed_steps:
                result.completed_steps.append(step_id)
            self.memory_manager.mark_step_completed(session_id, step_id)
        else:
            if step_id not in result.failed_steps:
                result.failed_steps.append(step_id)
            error_msg = f"Step {step_id} failed after {attempts} attempts. Last error: {last_error}"
            result.errors.append(error_msg)
            self.memory_manager.mark_step_failed(session_id, step_id)
