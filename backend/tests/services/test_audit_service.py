"""Tests for AuditService."""
import pytest
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

from app.models.audit_log import EventType
from app.services.audit_service import AuditService


@pytest.mark.asyncio
class TestAuditService:
    """Tests for AuditService."""

    async def test_log_event_basic(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test basic log_event functionality."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        with patch('app.services.audit_service.datetime') as mock_datetime:
            mock_now = datetime(2026, 2, 4, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            log = await service.log_event(
                event_type=EventType.USER_LOGIN,
                user_id="user-123",
                target_type="user",
                target_id="user-123",
                dynamodb=dynamodb,
            )

        assert log.log_id.startswith("log_")
        assert len(log.log_id) == 16  # "log_" + 12 hex chars
        assert log.timestamp == mock_now
        assert log.event_type == EventType.USER_LOGIN
        assert log.user_id == "user-123"
        assert log.target_type == "user"
        assert log.target_id == "user-123"
        assert log.details == {}
        assert log.request_id is None

    async def test_log_event_with_details(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_event with details and request_id."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_event(
            event_type=EventType.DATASET_CREATED,
            user_id="user-456",
            target_type="dataset",
            target_id="ds-001",
            dynamodb=dynamodb,
            details={"name": "Test Dataset", "rows": 100},
            request_id="req-789",
        )

        assert log.details == {"name": "Test Dataset", "rows": 100}
        assert log.request_id == "req-789"

    async def test_log_event_error_non_propagating(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test that DB errors do not propagate from log_event."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        # Mock repository to raise an exception
        with patch('app.services.audit_service.AuditLogRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.create.side_effect = Exception("DynamoDB error")
            mock_repo_class.return_value = mock_repo

            # Should not raise exception
            log = await service.log_event(
                event_type=EventType.USER_LOGIN,
                user_id="user-999",
                target_type="user",
                target_id="user-999",
                dynamodb=dynamodb,
            )

            assert log is None

    async def test_log_user_login(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_user_login convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_user_login(user_id="user-login", dynamodb=dynamodb)

        assert log.event_type == EventType.USER_LOGIN
        assert log.user_id == "user-login"
        assert log.target_type == "user"
        assert log.target_id == "user-login"

    async def test_log_user_logout(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_user_logout convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_user_logout(user_id="user-logout", dynamodb=dynamodb)

        assert log.event_type == EventType.USER_LOGOUT
        assert log.user_id == "user-logout"

    async def test_log_user_login_failed(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_user_login_failed convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_user_login_failed(
            email="test@example.com",
            reason="invalid_password",
            dynamodb=dynamodb,
        )

        assert log.event_type == EventType.USER_LOGIN_FAILED
        assert log.user_id == "unknown"  # DynamoDB GSI keys cannot be empty
        assert log.target_type == "email"
        assert log.target_id == "test@example.com"
        assert log.details == {"reason": "invalid_password"}

    async def test_log_dashboard_share_added(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_dashboard_share_added convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_dashboard_share_added(
            user_id="user-owner",
            dashboard_id="dash-001",
            shared_to_type="user",
            shared_to_id="user-viewer",
            permission="view",
            dynamodb=dynamodb,
        )

        assert log.event_type == EventType.DASHBOARD_SHARE_ADDED
        assert log.target_type == "dashboard"
        assert log.target_id == "dash-001"
        assert log.details["shared_to_type"] == "user"
        assert log.details["shared_to_id"] == "user-viewer"
        assert log.details["permission"] == "view"

    async def test_log_dataset_created(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_dataset_created convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_dataset_created(
            user_id="user-creator",
            dataset_id="ds-new",
            dataset_name="New Dataset",
            dynamodb=dynamodb,
        )

        assert log.event_type == EventType.DATASET_CREATED
        assert log.target_type == "dataset"
        assert log.target_id == "ds-new"
        assert log.details == {"name": "New Dataset"}

    async def test_log_dataset_imported(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_dataset_imported convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_dataset_imported(
            user_id="user-importer",
            dataset_id="ds-imported",
            dataset_name="Imported Data",
            source_type="s3_csv",
            dynamodb=dynamodb,
        )

        assert log.event_type == EventType.DATASET_IMPORTED
        assert log.details["source_type"] == "s3_csv"

    async def test_log_dataset_deleted(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_dataset_deleted convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_dataset_deleted(
            user_id="user-deleter",
            dataset_id="ds-deleted",
            dataset_name="Deleted Dataset",
            dynamodb=dynamodb,
        )

        assert log.event_type == EventType.DATASET_DELETED

    async def test_log_transform_executed(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_transform_executed convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_transform_executed(
            user_id="user-exec",
            transform_id="tf-001",
            execution_id="exec-001",
            dynamodb=dynamodb,
        )

        assert log.event_type == EventType.TRANSFORM_EXECUTED
        assert log.target_type == "transform"
        assert log.target_id == "tf-001"
        assert log.details == {"execution_id": "exec-001"}

    async def test_log_transform_failed(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_transform_failed convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_transform_failed(
            user_id="user-tf",
            transform_id="tf-fail",
            error="SQL syntax error",
            dynamodb=dynamodb,
        )

        assert log.event_type == EventType.TRANSFORM_FAILED
        assert log.details == {"error": "SQL syntax error"}

    async def test_log_card_execution_failed(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test log_card_execution_failed convenience method."""
        tables, dynamodb = dynamodb_tables
        service = AuditService()

        log = await service.log_card_execution_failed(
            user_id="user-card",
            card_id="card-fail",
            error="Runtime error",
            dynamodb=dynamodb,
        )

        assert log.event_type == EventType.CARD_EXECUTION_FAILED
        assert log.target_type == "card"
        assert log.target_id == "card-fail"
        assert log.details == {"error": "Runtime error"}
