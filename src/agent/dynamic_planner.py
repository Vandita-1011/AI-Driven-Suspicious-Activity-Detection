"""
Dynamic Planner
===============
Generates structured execution plans by mapping recognized patterns to a 
catalog of logical plan templates.
"""
from __future__ import annotations

import copy
import uuid
from typing import Dict, List

from src.agent.pattern_models import (
    ConfidenceLevel,
    InvestigationPatternType,
    PatternIdentificationResult,
)
from src.agent.plan_models import (
    ExecutionPlan,
    LogicalTool,
    PlanStep,
    StepPriority,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

ENTITY_FIELD_MAP = {
    "customer_ids": "customer_ids",
    "transaction_ids": "transaction_ids",
    "countries": "countries",
    "limit": "limit"
}


# ---------------------------------------------------------------------------
# Base templates for core patterns
# ---------------------------------------------------------------------------

_CORE_ENGINES = [
    PlanStep(
        step_id="rule_engine", description="Run Rule Engine",
        logical_tool=LogicalTool.RUN_RULE_ENGINE, dependencies=["load_txns"]
    ),
    PlanStep(
        step_id="behaviour_engine", description="Run Behaviour Engine",
        logical_tool=LogicalTool.RUN_BEHAVIOUR_ENGINE, dependencies=["load_txns", "load_cust"]
    ),
    PlanStep(
        step_id="statistical_engine", description="Run Statistical Engine",
        logical_tool=LogicalTool.RUN_STATISTICAL_ENGINE, dependencies=["load_txns"]
    ),
    PlanStep(
        step_id="ml_engine", description="Run ML Anomaly Engine",
        logical_tool=LogicalTool.RUN_ML_ENGINE, dependencies=["load_txns"]
    ),
    PlanStep(
        step_id="pattern_engine", description="Run AML Pattern Engine",
        logical_tool=LogicalTool.RUN_PATTERN_ENGINE, dependencies=["load_txns"]
    ),
]

_POST_PROCESSING = [
    PlanStep(
        step_id="risk_fusion", description="Smart Risk Fusion",
        logical_tool=LogicalTool.RUN_RISK_FUSION,
        dependencies=["rule_engine", "behaviour_engine", "statistical_engine", "ml_engine", "pattern_engine"]
    ),
    PlanStep(
        step_id="explainability", description="Generate Explanations",
        logical_tool=LogicalTool.RUN_EXPLAINABILITY, dependencies=["risk_fusion"]
    ),
    PlanStep(
        step_id="recommendation", description="Generate Recommendations",
        logical_tool=LogicalTool.RUN_RECOMMENDATION, dependencies=["explainability"]
    ),
    PlanStep(
        step_id="alert_prioritizer", description="Prioritize Alerts",
        logical_tool=LogicalTool.RUN_ALERT_PRIORITIZER, dependencies=["recommendation"]
    )
]

# ---------------------------------------------------------------------------
# Plan Template Catalog
# ---------------------------------------------------------------------------

PLAN_TEMPLATES: Dict[InvestigationPatternType, List[PlanStep]] = {
    InvestigationPatternType.CUSTOMER_INVESTIGATION: [
        PlanStep(
            step_id="load_cust", description="Load Customer Profile",
            logical_tool=LogicalTool.LOAD_CUSTOMER, required_inputs={"customer_ids": None}
        ),
        PlanStep(
            step_id="load_txns", description="Load Customer Transactions",
            logical_tool=LogicalTool.LOAD_TRANSACTIONS, required_inputs={"customer_ids": None}
        ),
        *_CORE_ENGINES,
        *_POST_PROCESSING,
    ],
    InvestigationPatternType.TRANSACTION_INVESTIGATION: [
        PlanStep(
            step_id="load_txns", description="Load Specific Transactions",
            logical_tool=LogicalTool.LOAD_TRANSACTIONS, required_inputs={"transaction_ids": None}
        ),
        PlanStep(
            step_id="load_cust", description="Load Associated Customers",
            logical_tool=LogicalTool.LOAD_CUSTOMER, dependencies=["load_txns"]
        ),
        *_CORE_ENGINES,
        *_POST_PROCESSING,
    ],
    InvestigationPatternType.GENERAL_SEARCH: [
        PlanStep(
            step_id="load_dataset", description="Load Full Dataset",
            logical_tool=LogicalTool.LOAD_DATASET
        ),
        PlanStep(
            step_id="load_txns", description="Load All Transactions",
            logical_tool=LogicalTool.LOAD_TRANSACTIONS, dependencies=["load_dataset"]
        ),
        PlanStep(
            step_id="load_cust", description="Load All Customers",
            logical_tool=LogicalTool.LOAD_CUSTOMER, dependencies=["load_dataset"]
        ),
        *_CORE_ENGINES,
        *_POST_PROCESSING,
    ]
}


class DynamicPlanner:
    """
    Generates structured logical execution plans based on identified patterns.
    """

    def generate_plan(self, pattern_result: PatternIdentificationResult) -> ExecutionPlan:
        """
        Creates an ExecutionPlan using the appropriate template and entity inputs.
        """
        logger.info("Generating plan for pattern: %s", pattern_result.investigation_pattern.value)

        # 1. Look up template
        if pattern_result.investigation_pattern not in PLAN_TEMPLATES:
            raise NotImplementedError(
                f"No plan template defined for pattern: {pattern_result.investigation_pattern.value}"
            )
        template = PLAN_TEMPLATES[pattern_result.investigation_pattern]

        # 2. Deep copy template to avoid mutating the static catalogue
        steps = copy.deepcopy(template)

        # 3. Inject entity values into required inputs dynamically
        for step in steps:
            for key in list(step.required_inputs.keys()):
                if key in ENTITY_FIELD_MAP:
                    entity_field = ENTITY_FIELD_MAP[key]
                    if hasattr(pattern_result.matched_entities, entity_field):
                        step.required_inputs[key] = getattr(pattern_result.matched_entities, entity_field)

        # 4. Insert manual validation step if confidence is LOW
        if pattern_result.confidence_level == ConfidenceLevel.LOW:
            logger.warning("Low confidence pattern identification. Inserting MANUAL_REVIEW step.")
            review_step = PlanStep(
                step_id="manual_review",
                description="Manual Review of Identified Plan",
                logical_tool=LogicalTool.MANUAL_REVIEW,
                dependencies=[],
                priority=StepPriority.HIGH,
                validation_constraints=["Requires user approval before proceeding"]
            )
            # Make the first actual data load steps depend on manual review
            for step in steps:
                if not step.dependencies:
                    step.dependencies.append("manual_review")
            steps.insert(0, review_step)

        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        plan = ExecutionPlan(
            plan_id=plan_id,
            pattern_type=pattern_result.investigation_pattern.value,
            steps=steps,
            metadata={
                "investigation_pattern": pattern_result.investigation_pattern.value,
                "confidence_score": pattern_result.confidence_score,
                "confidence_level": pattern_result.confidence_level.value,
                "reasoning": pattern_result.reasoning,
                "required_entities": pattern_result.required_entities,
                "missing_entities": pattern_result.missing_entities,
                "validation_messages": pattern_result.validation_messages
            }
        )

        logger.info("Generated ExecutionPlan %s with %d steps.", plan_id, len(steps))
        return plan
