"""
Tool Router
===========
Converts logical ExecutionPlans into RoutedPlans structured as parallel
execution stages based on dependency analysis.
"""
from __future__ import annotations

from typing import Dict, List, Set

from src.agent.plan_models import ExecutionPlan
from src.agent.routing_models import ExecutionStage, RoutedPlan, RoutedStep, StepStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ToolRouter:
    """
    Analyzes dependencies in an ExecutionPlan and organizes steps into
    sequential stages. All steps within a single stage can be executed
    in parallel.
    """

    def route(self, plan: ExecutionPlan) -> RoutedPlan:
        """
        Takes a logical ExecutionPlan and returns a RoutedPlan.
        Uses topological sorting (Kahn's algorithm) to build stages.
        """
        logger.info("Routing plan: %s", plan.plan_id)

        # 1. Wrap logical steps in RoutedStep and build dependency graph
        in_degree: Dict[str, int] = {step.step_id: 0 for step in plan.steps}
        adj_list: Dict[str, List[str]] = {step.step_id: [] for step in plan.steps}
        step_map: Dict[str, RoutedStep] = {}

        for plan_step in plan.steps:
            step_map[plan_step.step_id] = RoutedStep(plan_step=plan_step)
            for dep in plan_step.dependencies:
                # Ensure the dependency exists in the plan
                if dep in in_degree:
                    adj_list[dep].append(plan_step.step_id)
                    in_degree[plan_step.step_id] += 1
                else:
                    raise ValueError(
                        f"UnknownDependencyError: Step '{plan_step.step_id}' depends on unknown step '{dep}'"
                    )

        # 2. Iteratively extract nodes with 0 in-degree to form stages
        stages: List[ExecutionStage] = []
        stage_number = 1

        while True:
            # Find all steps with 0 remaining dependencies
            current_stage_ids = [step_id for step_id, degree in in_degree.items() if degree == 0]
            
            if not current_stage_ids:
                break

            current_stage_tools: List[RoutedStep] = []
            for step_id in current_stage_ids:
                routed_step = step_map[step_id]
                
                # Check for missing required inputs
                self._validate_inputs(routed_step)
                
                current_stage_tools.append(routed_step)

                # Remove this node from the graph
                in_degree[step_id] = -1  # Mark as processed
                for neighbor in adj_list[step_id]:
                    in_degree[neighbor] -= 1

            stages.append(ExecutionStage(stage_number=stage_number, tools=current_stage_tools))
            stage_number += 1

        # 3. Check for cycles (any node with degree > 0 means a cycle exists)
        unresolved = [step_id for step_id, degree in in_degree.items() if degree > 0]
        if unresolved:
            raise ValueError(f"Cyclic dependency detected in plan among steps: {unresolved}")

        routed_plan = RoutedPlan(plan_id=plan.plan_id, stages=stages)
        logger.info("Successfully routed plan into %d stages.", len(stages))
        return routed_plan

    def _validate_inputs(self, routed_step: RoutedStep) -> None:
        """
        Validates that required inputs are present.
        Only treats None, empty string, and empty lists as missing.
        """
        missing = []
        for k, v in routed_step.plan_step.required_inputs.items():
            if v is None or v == "" or v == []:
                missing.append(k)

        if missing:
            routed_step.status = StepStatus.BLOCKED
            logger.warning("Step %s blocked due to missing inputs: %s", routed_step.step_id, missing)
        else:
            # In a real execution engine, only stage 1 might be READY immediately,
            # but from a static routing perspective, it has all its static inputs.
            routed_step.status = StepStatus.READY
