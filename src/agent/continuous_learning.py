"""
Continuous Learning & Feedback Manager
======================================
Stores execution outcomes, investigator feedback, and metrics in memory
for future learning analysis. Performs no online model retraining or logic modification.
"""
from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, List, Optional

from src.agent.execution_models import ExecutionResult, ExecutionStatus
from src.agent.learning_models import FeedbackType, LearningRecord, LearningSummary
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ContinuousLearningManager:
    """
    In-memory state recorder for execution outcomes and investigator feedback.
    """

    def __init__(self) -> None:
        self._records: Dict[str, LearningRecord] = {}  # record_id -> record
        self._execution_to_record_id: Dict[str, str] = {}  # execution_id -> record_id

    def record_execution_result(
        self,
        execution_result: ExecutionResult,
        risk_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LearningRecord:
        """
        Records an execution result into memory as a LearningRecord.
        """
        if not execution_result:
            raise ValueError("Execution result cannot be None.")

        if not execution_result.execution_id:
            raise ValueError("Execution result must have a valid execution_id.")

        if execution_result.execution_id in self._execution_to_record_id:
            existing_id = self._execution_to_record_id[execution_result.execution_id]
            raise ValueError(
                f"Duplicate record: Execution ID '{execution_result.execution_id}' is already recorded with Record ID '{existing_id}'."
            )

        # Calculate duration
        duration = 0.0
        if execution_result.finished_at and execution_result.started_at:
            duration = max(
                0.0,
                (execution_result.finished_at - execution_result.started_at).total_seconds(),
            )

        record_id = f"rec_{uuid.uuid4().hex[:8]}"

        record = LearningRecord(
            record_id=record_id,
            session_id=execution_result.session_id,
            execution_id=execution_result.execution_id,
            plan_id=execution_result.plan_id,
            timestamp=datetime.datetime.utcnow(),
            execution_status=execution_result.status,
            completed_steps=list(execution_result.completed_steps),
            failed_steps=list(execution_result.failed_steps),
            execution_duration=duration,
            risk_score=risk_score,
            metadata=dict(metadata) if metadata else {},
        )

        self._records[record_id] = record
        self._execution_to_record_id[execution_result.execution_id] = record_id

        logger.info(
            "Recorded learning record %s for execution %s",
            record_id,
            execution_result.execution_id,
        )
        return record

    def record_feedback(
        self,
        execution_id: str,
        feedback_type: FeedbackType,
        investigator_notes: Optional[str] = None,
    ) -> LearningRecord:
        """
        Associates investigator feedback with an existing execution record.
        """
        if not execution_id or execution_id not in self._execution_to_record_id:
            raise ValueError(f"Unknown execution ID: '{execution_id}'")

        if not isinstance(feedback_type, FeedbackType):
            # Attempt string matching if passed string
            try:
                feedback_type = FeedbackType(feedback_type)
            except ValueError:
                raise ValueError(f"Invalid feedback type: '{feedback_type}'")

        record_id = self._execution_to_record_id[execution_id]
        record = self._records[record_id]

        record.feedback_type = feedback_type
        if investigator_notes is not None:
            record.investigator_notes = investigator_notes

        logger.info(
            "Recorded feedback %s for execution %s", feedback_type.value, execution_id
        )
        return record

    def get_learning_record(self, record_id: str) -> LearningRecord:
        """
        Retrieves a learning record by its record ID.
        """
        if record_id not in self._records:
            raise ValueError(f"Unknown record ID: '{record_id}'")
        return self._records[record_id]

    def get_execution_history(self, session_id: str) -> List[LearningRecord]:
        """
        Retrieves all historical learning records for a given session ID.
        """
        return [
            record
            for record in self._records.values()
            if record.session_id == session_id
        ]

    def generate_learning_summary(self) -> LearningSummary:
        """
        Computes aggregated summary statistics across all recorded executions.
        """
        records = list(self._records.values())
        total_records = len(records)

        if total_records == 0:
            return LearningSummary(
                total_records=0,
                successful_executions=0,
                failed_executions=0,
                partial_executions=0,
                cancelled_executions=0,
                feedback_distribution={fb.value: 0 for fb in FeedbackType},
                total_investigator_notes=0,
                average_execution_time=0.0,
                generated_at=datetime.datetime.utcnow(),
            )

        successful = sum(
            1 for r in records if r.execution_status == ExecutionStatus.COMPLETED
        )
        failed = sum(
            1 for r in records if r.execution_status == ExecutionStatus.FAILED
        )
        partial = sum(
            1 for r in records if r.execution_status == ExecutionStatus.PARTIAL_SUCCESS
        )
        cancelled = sum(
            1 for r in records if r.execution_status == ExecutionStatus.CANCELLED
        )

        feedback_dist = {fb.value: 0 for fb in FeedbackType}
        notes_count = 0

        for r in records:
            if r.feedback_type:
                feedback_dist[r.feedback_type.value] = (
                    feedback_dist.get(r.feedback_type.value, 0) + 1
                )
            if r.investigator_notes:
                notes_count += 1

        avg_time = sum(r.execution_duration for r in records) / total_records

        return LearningSummary(
            total_records=total_records,
            successful_executions=successful,
            failed_executions=failed,
            partial_executions=partial,
            cancelled_executions=cancelled,
            feedback_distribution=feedback_dist,
            total_investigator_notes=notes_count,
            average_execution_time=round(avg_time, 4),
            generated_at=datetime.datetime.utcnow(),
        )
