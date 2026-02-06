"""Tests for TransformExecution model."""
from datetime import datetime, timedelta
import pytest
from pydantic import ValidationError
from app.models.transform_execution import TransformExecution


class TestTransformExecution:
    """Test TransformExecution model."""

    def test_transform_execution_valid_running(self):
        """Test creating TransformExecution with valid running status."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="running",
            started_at=now,
            triggered_by="manual"
        )

        assert execution.execution_id == "exec-123"
        assert execution.transform_id == "transform-456"
        assert execution.status == "running"
        assert execution.started_at == now
        assert execution.triggered_by == "manual"
        assert execution.finished_at is None
        assert execution.duration_ms is None
        assert execution.output_row_count is None
        assert execution.output_dataset_id is None
        assert execution.error is None

    def test_transform_execution_valid_success(self):
        """Test creating TransformExecution with valid success status."""
        started = datetime.utcnow()
        finished = started + timedelta(seconds=5)

        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="success",
            started_at=started,
            finished_at=finished,
            duration_ms=5000.0,
            output_row_count=1500,
            output_dataset_id="dataset-output-789",
            triggered_by="schedule"
        )

        assert execution.status == "success"
        assert execution.finished_at == finished
        assert execution.duration_ms == 5000.0
        assert execution.output_row_count == 1500
        assert execution.output_dataset_id == "dataset-output-789"
        assert execution.error is None

    def test_transform_execution_valid_failed(self):
        """Test creating TransformExecution with valid failed status."""
        started = datetime.utcnow()
        finished = started + timedelta(seconds=2)

        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="failed",
            started_at=started,
            finished_at=finished,
            duration_ms=2000.0,
            error="Division by zero in transform code",
            triggered_by="manual"
        )

        assert execution.status == "failed"
        assert execution.error == "Division by zero in transform code"
        assert execution.output_row_count is None
        assert execution.output_dataset_id is None

    def test_transform_execution_triggered_by_manual(self):
        """Test TransformExecution with triggered_by='manual'."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="running",
            started_at=now,
            triggered_by="manual"
        )

        assert execution.triggered_by == "manual"

    def test_transform_execution_triggered_by_schedule(self):
        """Test TransformExecution with triggered_by='schedule'."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="success",
            started_at=now,
            triggered_by="schedule"
        )

        assert execution.triggered_by == "schedule"

    def test_transform_execution_missing_execution_id(self):
        """Test TransformExecution validation fails without execution_id."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            TransformExecution(
                transform_id="transform-456",
                status="running",
                started_at=now,
                triggered_by="manual"
            )

    def test_transform_execution_missing_transform_id(self):
        """Test TransformExecution validation fails without transform_id."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            TransformExecution(
                execution_id="exec-123",
                status="running",
                started_at=now,
                triggered_by="manual"
            )

    def test_transform_execution_missing_status(self):
        """Test TransformExecution validation fails without status."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            TransformExecution(
                execution_id="exec-123",
                transform_id="transform-456",
                started_at=now,
                triggered_by="manual"
            )

    def test_transform_execution_missing_started_at(self):
        """Test TransformExecution validation fails without started_at."""
        with pytest.raises(ValidationError):
            TransformExecution(
                execution_id="exec-123",
                transform_id="transform-456",
                status="running",
                triggered_by="manual"
            )

    def test_transform_execution_missing_triggered_by(self):
        """Test TransformExecution validation fails without triggered_by."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            TransformExecution(
                execution_id="exec-123",
                transform_id="transform-456",
                status="running",
                started_at=now
            )

    def test_transform_execution_default_optional_fields(self):
        """Test TransformExecution with default values for optional fields."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="running",
            started_at=now,
            triggered_by="manual"
        )

        assert execution.finished_at is None
        assert execution.duration_ms is None
        assert execution.output_row_count is None
        assert execution.output_dataset_id is None
        assert execution.error is None

    def test_transform_execution_serialization(self):
        """Test TransformExecution serialization to dict."""
        started = datetime.utcnow()
        finished = started + timedelta(seconds=3)

        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="success",
            started_at=started,
            finished_at=finished,
            duration_ms=3000.0,
            output_row_count=2500,
            output_dataset_id="dataset-output-789",
            triggered_by="schedule"
        )

        execution_dict = execution.model_dump()
        assert execution_dict["execution_id"] == "exec-123"
        assert execution_dict["transform_id"] == "transform-456"
        assert execution_dict["status"] == "success"
        assert execution_dict["started_at"] == started
        assert execution_dict["finished_at"] == finished
        assert execution_dict["duration_ms"] == 3000.0
        assert execution_dict["output_row_count"] == 2500
        assert execution_dict["output_dataset_id"] == "dataset-output-789"
        assert execution_dict["triggered_by"] == "schedule"
        assert execution_dict["error"] is None

    def test_transform_execution_from_orm(self):
        """Test TransformExecution can be created from ORM attributes."""
        # This tests the ConfigDict(from_attributes=True) configuration
        class MockORM:
            """Mock ORM object for testing."""
            execution_id = "exec-123"
            transform_id = "transform-456"
            status = "success"
            started_at = datetime.utcnow()
            finished_at = started_at + timedelta(seconds=1)
            duration_ms = 1000.0
            output_row_count = 100
            output_dataset_id = "dataset-output"
            error = None
            triggered_by = "manual"

        mock_orm = MockORM()
        execution = TransformExecution.model_validate(mock_orm)

        assert execution.execution_id == "exec-123"
        assert execution.transform_id == "transform-456"
        assert execution.status == "success"

    def test_transform_execution_with_zero_duration(self):
        """Test TransformExecution with zero duration (very fast execution)."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="success",
            started_at=now,
            finished_at=now,
            duration_ms=0.0,
            output_row_count=0,
            triggered_by="manual"
        )

        assert execution.duration_ms == 0.0
        assert execution.output_row_count == 0

    def test_transform_execution_with_large_output(self):
        """Test TransformExecution with large output row count."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="success",
            started_at=now,
            output_row_count=10_000_000,
            triggered_by="schedule"
        )

        assert execution.output_row_count == 10_000_000

    def test_transform_execution_with_long_error_message(self):
        """Test TransformExecution with long error message."""
        now = datetime.utcnow()
        long_error = "Error: " + "x" * 1000

        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="failed",
            started_at=now,
            error=long_error,
            triggered_by="manual"
        )

        assert execution.error == long_error
        assert len(execution.error) > 1000

    def test_transform_execution_status_running_without_finished_data(self):
        """Test running status should not have finished_at or output data."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="running",
            started_at=now,
            triggered_by="manual"
        )

        assert execution.status == "running"
        assert execution.finished_at is None
        assert execution.duration_ms is None
        assert execution.output_row_count is None

    def test_transform_execution_status_success_with_output_dataset(self):
        """Test success status with output dataset ID."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="success",
            started_at=now,
            output_dataset_id="dataset-output-new",
            output_row_count=500,
            triggered_by="schedule"
        )

        assert execution.status == "success"
        assert execution.output_dataset_id == "dataset-output-new"
        assert execution.error is None

    def test_transform_execution_status_failed_with_error(self):
        """Test failed status with error message."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="failed",
            started_at=now,
            error="Input dataset not found",
            triggered_by="manual"
        )

        assert execution.status == "failed"
        assert execution.error == "Input dataset not found"
        assert execution.output_dataset_id is None

    def test_transform_execution_with_fractional_duration(self):
        """Test TransformExecution with fractional milliseconds duration."""
        now = datetime.utcnow()
        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="success",
            started_at=now,
            duration_ms=1234.567,
            triggered_by="manual"
        )

        assert execution.duration_ms == 1234.567

    def test_transform_execution_multiple_instances(self):
        """Test creating multiple TransformExecution instances with different IDs."""
        now = datetime.utcnow()

        exec1 = TransformExecution(
            execution_id="exec-001",
            transform_id="transform-456",
            status="success",
            started_at=now,
            triggered_by="manual"
        )

        exec2 = TransformExecution(
            execution_id="exec-002",
            transform_id="transform-456",
            status="running",
            started_at=now,
            triggered_by="schedule"
        )

        assert exec1.execution_id != exec2.execution_id
        assert exec1.transform_id == exec2.transform_id
        assert exec1.triggered_by != exec2.triggered_by

    def test_transform_execution_datetime_precision(self):
        """Test TransformExecution preserves datetime precision."""
        precise_time = datetime(2024, 1, 15, 10, 30, 45, 123456)

        execution = TransformExecution(
            execution_id="exec-123",
            transform_id="transform-456",
            status="running",
            started_at=precise_time,
            triggered_by="manual"
        )

        assert execution.started_at == precise_time
        assert execution.started_at.microsecond == 123456
