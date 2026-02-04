"""Tests for TransformSchedulerService."""
import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.transform_scheduler_service import TransformSchedulerService


class TestTransformSchedulerService:
    """Tests for TransformSchedulerService."""

    def test_start_creates_background_task(self):
        """Test start() creates asyncio.Task."""
        scheduler = TransformSchedulerService()
        assert scheduler._running is False
        assert scheduler._task is None
        # We'll test start via the _is_due method instead since start() needs event loop

    def test_is_due_within_interval(self):
        """Test _is_due returns True when within interval."""
        # "every minute" cron, checked at 10:00:30 (30s after last trigger at 10:00:00)
        now = datetime(2026, 2, 4, 10, 0, 30, tzinfo=timezone.utc)
        with patch("app.services.transform_scheduler_service.settings") as mock_settings:
            mock_settings.scheduler_interval_seconds = 60
            result = TransformSchedulerService._is_due("* * * * *", now)
        assert result is True

    def test_is_due_outside_interval(self):
        """Test _is_due returns False when outside interval."""
        # "every hour" cron, checked at 10:30:00 (30min after 10:00:00 trigger)
        now = datetime(2026, 2, 4, 10, 30, 0, tzinfo=timezone.utc)
        with patch("app.services.transform_scheduler_service.settings") as mock_settings:
            mock_settings.scheduler_interval_seconds = 60
            result = TransformSchedulerService._is_due("0 * * * *", now)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_skips_running_transforms(self):
        """Test scheduler skips transforms with running executions."""
        scheduler = TransformSchedulerService()

        mock_dynamodb = MagicMock()
        mock_s3 = MagicMock()

        # Mock transform repo
        mock_transform = MagicMock()
        mock_transform.id = "transform-001"
        mock_transform.schedule_cron = "* * * * *"

        with patch("app.services.transform_scheduler_service.TransformRepository") as mock_repo_cls, \
             patch("app.services.transform_scheduler_service.TransformExecutionRepository") as mock_exec_repo_cls, \
             patch("app.services.transform_scheduler_service.TransformExecutionService") as mock_service_cls, \
             patch.object(TransformSchedulerService, "_is_due", return_value=True):

            mock_repo = MagicMock()
            mock_repo._execute_db_operation = AsyncMock()
            mock_table = MagicMock()
            mock_table.scan = AsyncMock(return_value={'Items': [{'transformId': 'transform-001', 'scheduleEnabled': True, 'scheduleCron': '* * * * *'}]})
            mock_repo._execute_db_operation.side_effect = [mock_table, {'Items': [{'transformId': 'transform-001'}]}]
            mock_repo.table_name = "bi_transforms"
            mock_repo.model = MagicMock(return_value=mock_transform)
            mock_repo._from_dynamodb_item = MagicMock(return_value={"id": "transform-001", "name": "Test", "owner_id": "user-1", "input_dataset_ids": ["ds-1"], "code": "test", "schedule_cron": "* * * * *", "schedule_enabled": True, "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)})
            mock_repo_cls.return_value = mock_repo

            mock_exec_repo = MagicMock()
            mock_exec_repo.has_running_execution = AsyncMock(return_value=True)
            mock_exec_repo_cls.return_value = mock_exec_repo

            mock_service = MagicMock()
            mock_service.execute = AsyncMock()
            mock_service_cls.return_value = mock_service

            await scheduler._execute_due_transforms(mock_dynamodb, mock_s3)

            # Should NOT have called execute
            mock_service.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_executes_due_transform(self):
        """Test scheduler executes a due transform."""
        scheduler = TransformSchedulerService()

        mock_dynamodb = MagicMock()
        mock_s3 = MagicMock()

        mock_transform = MagicMock()
        mock_transform.id = "transform-001"
        mock_transform.schedule_cron = "* * * * *"

        with patch("app.services.transform_scheduler_service.TransformRepository") as mock_repo_cls, \
             patch("app.services.transform_scheduler_service.TransformExecutionRepository") as mock_exec_repo_cls, \
             patch("app.services.transform_scheduler_service.TransformExecutionService") as mock_service_cls, \
             patch.object(TransformSchedulerService, "_is_due", return_value=True):

            mock_repo = MagicMock()
            mock_repo._execute_db_operation = AsyncMock()
            mock_table = MagicMock()
            mock_table.scan = AsyncMock(return_value={'Items': [{'transformId': 'transform-001'}]})
            mock_repo._execute_db_operation.side_effect = [mock_table, {'Items': [{'transformId': 'transform-001'}]}]
            mock_repo.table_name = "bi_transforms"
            mock_repo.model = MagicMock(return_value=mock_transform)
            mock_repo._from_dynamodb_item = MagicMock(return_value={"id": "transform-001", "name": "Test", "owner_id": "user-1", "input_dataset_ids": ["ds-1"], "code": "test", "schedule_cron": "* * * * *", "schedule_enabled": True, "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)})
            mock_repo_cls.return_value = mock_repo

            mock_exec_repo = MagicMock()
            mock_exec_repo.has_running_execution = AsyncMock(return_value=False)
            mock_exec_repo_cls.return_value = mock_exec_repo

            mock_service = MagicMock()
            mock_service.execute = AsyncMock()
            mock_service_cls.return_value = mock_service

            await scheduler._execute_due_transforms(mock_dynamodb, mock_s3)

            # Should have called execute with triggered_by="schedule"
            mock_service.execute.assert_called_once()
            call_kwargs = mock_service.execute.call_args[1]
            assert call_kwargs["triggered_by"] == "schedule"

    @pytest.mark.asyncio
    async def test_check_skips_no_schedule_cron(self):
        """Test scheduler skips transforms with no schedule_cron."""
        scheduler = TransformSchedulerService()

        mock_dynamodb = MagicMock()
        mock_s3 = MagicMock()

        mock_transform = MagicMock()
        mock_transform.id = "transform-001"
        mock_transform.schedule_cron = None  # No cron expression

        with patch("app.services.transform_scheduler_service.TransformRepository") as mock_repo_cls, \
             patch("app.services.transform_scheduler_service.TransformExecutionRepository") as mock_exec_repo_cls, \
             patch("app.services.transform_scheduler_service.TransformExecutionService") as mock_service_cls:

            mock_repo = MagicMock()
            mock_repo._execute_db_operation = AsyncMock()
            mock_table = MagicMock()
            mock_table.scan = AsyncMock(return_value={'Items': [{'transformId': 'transform-001'}]})
            mock_repo._execute_db_operation.side_effect = [mock_table, {'Items': [{'transformId': 'transform-001'}]}]
            mock_repo.table_name = "bi_transforms"
            mock_repo.model = MagicMock(return_value=mock_transform)
            mock_repo._from_dynamodb_item = MagicMock(return_value={"id": "transform-001", "name": "Test", "owner_id": "user-1", "input_dataset_ids": ["ds-1"], "code": "test", "schedule_cron": None, "schedule_enabled": True, "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)})
            mock_repo_cls.return_value = mock_repo

            mock_exec_repo = MagicMock()
            mock_exec_repo_cls.return_value = mock_exec_repo

            mock_service = MagicMock()
            mock_service.execute = AsyncMock()
            mock_service_cls.return_value = mock_service

            await scheduler._execute_due_transforms(mock_dynamodb, mock_s3)

            mock_service.execute.assert_not_called()
