"""Tests for TransformExecutionRepository."""
import pytest
from datetime import datetime, timezone
from typing import Any

from app.models.transform_execution import TransformExecution
from app.repositories.transform_execution_repository import TransformExecutionRepository


@pytest.mark.asyncio
class TestTransformExecutionRepository:
    """Tests for TransformExecutionRepository."""

    async def test_create_execution(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test creating an execution record."""
        tables, dynamodb = dynamodb_tables
        repo = TransformExecutionRepository()
        data = {
            "execution_id": "exec-001",
            "transform_id": "transform-001",
            "status": "running",
            "started_at": datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc),
            "triggered_by": "manual",
        }
        result = await repo.create(data, dynamodb)
        assert result.execution_id == "exec-001"
        assert result.transform_id == "transform-001"
        assert result.status == "running"
        assert result.triggered_by == "manual"

    async def test_update_status_success(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test updating execution from running to success."""
        tables, dynamodb = dynamodb_tables
        repo = TransformExecutionRepository()
        started_at = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 2, 4, 10, 0, 5, tzinfo=timezone.utc)
        # Create first
        await repo.create({
            "execution_id": "exec-002",
            "transform_id": "transform-002",
            "status": "running",
            "started_at": started_at,
            "triggered_by": "manual",
        }, dynamodb)
        # Update to success
        await repo.update_status(
            "transform-002", started_at,
            {"status": "success", "finished_at": finished_at, "duration_ms": 5000.0, "output_row_count": 100, "output_dataset_id": "ds-out-001"},
            dynamodb,
        )
        # Verify
        executions = await repo.list_by_transform("transform-002", dynamodb)
        assert len(executions) == 1
        assert executions[0].status == "success"
        assert executions[0].duration_ms == 5000.0
        assert executions[0].output_row_count == 100

    async def test_update_status_failed(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test updating execution from running to failed."""
        tables, dynamodb = dynamodb_tables
        repo = TransformExecutionRepository()
        started_at = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        await repo.create({
            "execution_id": "exec-003",
            "transform_id": "transform-003",
            "status": "running",
            "started_at": started_at,
            "triggered_by": "manual",
        }, dynamodb)
        await repo.update_status(
            "transform-003", started_at,
            {"status": "failed", "finished_at": datetime(2026, 2, 4, 10, 0, 3, tzinfo=timezone.utc), "duration_ms": 3000.0, "error": "SQL error"},
            dynamodb,
        )
        executions = await repo.list_by_transform("transform-003", dynamodb)
        assert len(executions) == 1
        assert executions[0].status == "failed"
        assert executions[0].error == "SQL error"

    async def test_list_by_transform(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test listing executions newest first."""
        tables, dynamodb = dynamodb_tables
        repo = TransformExecutionRepository()
        # Create multiple executions
        for i in range(3):
            await repo.create({
                "execution_id": f"exec-{i}",
                "transform_id": "transform-multi",
                "status": "success",
                "started_at": datetime(2026, 2, 4, 10+i, 0, 0, tzinfo=timezone.utc),
                "triggered_by": "manual",
            }, dynamodb)
        executions = await repo.list_by_transform("transform-multi", dynamodb)
        assert len(executions) == 3
        # Newest first (ScanIndexForward=False)
        assert executions[0].started_at > executions[1].started_at
        assert executions[1].started_at > executions[2].started_at

    async def test_list_by_transform_empty(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test listing with no executions returns empty list."""
        tables, dynamodb = dynamodb_tables
        repo = TransformExecutionRepository()
        executions = await repo.list_by_transform("nonexistent", dynamodb)
        assert executions == []

    async def test_has_running_execution_true(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test detecting running execution."""
        tables, dynamodb = dynamodb_tables
        repo = TransformExecutionRepository()
        await repo.create({
            "execution_id": "exec-running",
            "transform_id": "transform-running",
            "status": "running",
            "started_at": datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc),
            "triggered_by": "manual",
        }, dynamodb)
        assert await repo.has_running_execution("transform-running", dynamodb) is True

    async def test_has_running_execution_false(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test no running execution when all completed."""
        tables, dynamodb = dynamodb_tables
        repo = TransformExecutionRepository()
        await repo.create({
            "execution_id": "exec-done",
            "transform_id": "transform-done",
            "status": "success",
            "started_at": datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc),
            "triggered_by": "manual",
        }, dynamodb)
        assert await repo.has_running_execution("transform-done", dynamodb) is False
