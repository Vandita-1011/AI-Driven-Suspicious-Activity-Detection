# pyrefly: ignore [missing-import]
import datetime
import pytest

from src.agent.continuous_learning import ContinuousLearningManager
from src.agent.execution_models import ExecutionResult, ExecutionStatus
from src.agent.learning_models import FeedbackType, LearningRecord, LearningSummary


@pytest.fixture
def manager() -> ContinuousLearningManager:
    return ContinuousLearningManager()


def _mock_execution_result(
    execution_id: str = "exec_1",
    session_id: str = "sess_1",
    status: ExecutionStatus = ExecutionStatus.COMPLETED,
    duration_seconds: float = 2.5,
) -> ExecutionResult:
    start = datetime.datetime.utcnow()
    finish = start + datetime.timedelta(seconds=duration_seconds)
    return ExecutionResult(
        execution_id=execution_id,
        session_id=session_id,
        plan_id="plan_1",
        status=status,
        started_at=start,
        finished_at=finish,
        completed_steps=["s1", "s2"] if status != ExecutionStatus.FAILED else [],
        failed_steps=["s1"] if status == ExecutionStatus.FAILED else [],
        execution_log=[],
        errors=["error"] if status == ExecutionStatus.FAILED else [],
    )


class TestContinuousLearningManager:

    def test_record_successful_execution(self, manager):
        exec_res = _mock_execution_result(status=ExecutionStatus.COMPLETED)
        record = manager.record_execution_result(exec_res, risk_score=0.85)

        assert record.record_id.startswith("rec_")
        assert record.execution_id == exec_res.execution_id
        assert record.execution_status == ExecutionStatus.COMPLETED
        assert record.risk_score == 0.85
        assert record.execution_duration >= 2.4

    def test_record_failed_execution(self, manager):
        exec_res = _mock_execution_result(status=ExecutionStatus.FAILED)
        record = manager.record_execution_result(exec_res)

        assert record.execution_status == ExecutionStatus.FAILED
        assert record.failed_steps == ["s1"]

    def test_record_partial_execution(self, manager):
        exec_res = _mock_execution_result(status=ExecutionStatus.PARTIAL_SUCCESS)
        record = manager.record_execution_result(exec_res)

        assert record.execution_status == ExecutionStatus.PARTIAL_SUCCESS

    def test_record_cancelled_execution(self, manager):
        exec_res = _mock_execution_result(status=ExecutionStatus.CANCELLED)
        record = manager.record_execution_result(exec_res)

        assert record.execution_status == ExecutionStatus.CANCELLED

    def test_record_investigator_feedback(self, manager):
        exec_res = _mock_execution_result(execution_id="exec_feedback")
        manager.record_execution_result(exec_res)

        updated_record = manager.record_feedback(
            execution_id="exec_feedback",
            feedback_type=FeedbackType.TRUE_POSITIVE,
            investigator_notes="Confirmed structuring pattern.",
        )

        assert updated_record.feedback_type == FeedbackType.TRUE_POSITIVE
        assert updated_record.investigator_notes == "Confirmed structuring pattern."

    def test_invalid_execution_id_feedback_raises_error(self, manager):
        with pytest.raises(ValueError, match="Unknown execution ID"):
            manager.record_feedback("non_existent_exec", FeedbackType.FALSE_POSITIVE)

    def test_invalid_feedback_type_raises_error(self, manager):
        exec_res = _mock_execution_result(execution_id="exec_invalid_fb")
        manager.record_execution_result(exec_res)

        with pytest.raises(ValueError, match="Invalid feedback type"):
            # pyrefly: ignore [arg-type]
            manager.record_feedback("exec_invalid_fb", "INVALID_FEEDBACK")

    def test_duplicate_execution_record_raises_error(self, manager):
        exec_res = _mock_execution_result(execution_id="exec_dup")
        manager.record_execution_result(exec_res)

        with pytest.raises(ValueError, match="Duplicate record"):
            manager.record_execution_result(exec_res)

    def test_missing_execution_result_raises_error(self, manager):
        with pytest.raises(ValueError, match="Execution result cannot be None"):
            # pyrefly: ignore [arg-type]
            manager.record_execution_result(None)

    def test_execution_history_retrieval(self, manager):
        res1 = _mock_execution_result(execution_id="e1", session_id="sess_A")
        res2 = _mock_execution_result(execution_id="e2", session_id="sess_A")
        res3 = _mock_execution_result(execution_id="e3", session_id="sess_B")

        manager.record_execution_result(res1)
        manager.record_execution_result(res2)
        manager.record_execution_result(res3)

        history_A = manager.get_execution_history("sess_A")
        assert len(history_A) == 2
        assert {r.execution_id for r in history_A} == {"e1", "e2"}

    def test_get_learning_record(self, manager):
        res = _mock_execution_result(execution_id="e1")
        record = manager.record_execution_result(res)

        fetched = manager.get_learning_record(record.record_id)
        assert fetched.record_id == record.record_id

    def test_get_unknown_learning_record_raises_error(self, manager):
        with pytest.raises(ValueError, match="Unknown record ID"):
            manager.get_learning_record("rec_unknown")

    def test_empty_history_summary(self, manager):
        summary = manager.generate_learning_summary()

        assert isinstance(summary, LearningSummary)
        assert summary.total_records == 0
        assert summary.successful_executions == 0
        assert summary.average_execution_time == 0.0

    def test_learning_summary_generation(self, manager):
        e1 = _mock_execution_result("e1", status=ExecutionStatus.COMPLETED, duration_seconds=1.0)
        e2 = _mock_execution_result("e2", status=ExecutionStatus.FAILED, duration_seconds=3.0)
        e3 = _mock_execution_result("e3", status=ExecutionStatus.PARTIAL_SUCCESS, duration_seconds=2.0)
        e4 = _mock_execution_result("e4", status=ExecutionStatus.CANCELLED, duration_seconds=0.0)

        manager.record_execution_result(e1)
        manager.record_execution_result(e2)
        manager.record_execution_result(e3)
        manager.record_execution_result(e4)

        manager.record_feedback("e1", FeedbackType.TRUE_POSITIVE, "Notes 1")
        manager.record_feedback("e2", FeedbackType.FALSE_POSITIVE, "Notes 2")
        manager.record_feedback("e3", FeedbackType.INVESTIGATOR_NOTE, "Notes 3")

        summary = manager.generate_learning_summary()

        assert summary.total_records == 4
        assert summary.successful_executions == 1
        assert summary.failed_executions == 1
        assert summary.partial_executions == 1
        assert summary.cancelled_executions == 1
        assert summary.feedback_distribution[FeedbackType.TRUE_POSITIVE.value] == 1
        assert summary.feedback_distribution[FeedbackType.FALSE_POSITIVE.value] == 1
        assert summary.total_investigator_notes == 3
        assert summary.average_execution_time == 1.5  # (1+3+2+0)/4 = 1.5
