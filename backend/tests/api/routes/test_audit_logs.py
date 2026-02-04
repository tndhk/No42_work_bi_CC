"""Audit Logs API endpoint tests."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource
from app.models.user import User
from app.models.audit_log import AuditLog, EventType
from app.repositories import audit_log_repository


@pytest.fixture
def admin_user():
    return User(
        id="admin_1",
        email="admin@example.com",
        role="admin",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def regular_user():
    return User(
        id="user_1",
        email="user@example.com",
        role="user",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_dynamodb():
    return MagicMock()


def _make_client(user, mock_dynamodb):
    async def override_get_current_user():
        return user
    async def override_get_dynamodb_resource():
        yield mock_dynamodb
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_dynamodb_resource] = override_get_dynamodb_resource
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(admin_user, mock_dynamodb):
    yield from _make_client(admin_user, mock_dynamodb)


@pytest.fixture
def regular_client(regular_user, mock_dynamodb):
    yield from _make_client(regular_user, mock_dynamodb)


@pytest.fixture
def sample_audit_logs():
    now = datetime.now(timezone.utc)
    return [
        AuditLog(
            log_id="log_abc001",
            timestamp=now,
            event_type=EventType.USER_LOGIN,
            user_id="user_1",
            target_type="user",
            target_id="user_1",
            details={},
        ),
        AuditLog(
            log_id="log_abc002",
            timestamp=now,
            event_type=EventType.DATASET_CREATED,
            user_id="user_2",
            target_type="dataset",
            target_id="ds_001",
            details={"name": "test_dataset"},
        ),
        AuditLog(
            log_id="log_abc003",
            timestamp=now,
            event_type=EventType.USER_LOGIN,
            user_id="user_1",
            target_type="user",
            target_id="user_1",
            details={},
        ),
    ]


class TestListAuditLogs:
    def test_list_audit_logs_admin_success(self, admin_client, sample_audit_logs):
        """Admin can retrieve audit log list."""
        async def mock_list_all(self, dynamodb, **kwargs):
            return sample_audit_logs
        with patch.object(audit_log_repository.AuditLogRepository, 'list_all', mock_list_all):
            response = admin_client.get("/api/audit-logs")
            assert response.status_code == 200
            body = response.json()
            assert "data" in body
            assert len(body["data"]) == 3
            assert "pagination" in body
            assert body["pagination"]["total"] == 3

    def test_list_audit_logs_forbidden_for_regular_user(self, regular_client):
        """Regular user gets 403 when trying to access audit logs."""
        response = regular_client.get("/api/audit-logs")
        assert response.status_code == 403

    def test_list_audit_logs_with_event_type_filter(self, admin_client, sample_audit_logs):
        """Filtering by event_type query parameter works."""
        filtered = [log for log in sample_audit_logs if log.event_type == EventType.USER_LOGIN]

        async def mock_list_all(self, dynamodb, **kwargs):
            assert kwargs.get("event_type") == EventType.USER_LOGIN
            return filtered
        with patch.object(audit_log_repository.AuditLogRepository, 'list_all', mock_list_all):
            response = admin_client.get("/api/audit-logs?event_type=USER_LOGIN")
            assert response.status_code == 200
            body = response.json()
            assert len(body["data"]) == 2
            for item in body["data"]:
                assert item["event_type"] == "USER_LOGIN"

    def test_list_audit_logs_with_user_id_filter(self, admin_client, sample_audit_logs):
        """Filtering by user_id query parameter works."""
        filtered = [log for log in sample_audit_logs if log.user_id == "user_2"]

        async def mock_list_all(self, dynamodb, **kwargs):
            assert kwargs.get("user_id") == "user_2"
            return filtered
        with patch.object(audit_log_repository.AuditLogRepository, 'list_all', mock_list_all):
            response = admin_client.get("/api/audit-logs?user_id=user_2")
            assert response.status_code == 200
            body = response.json()
            assert len(body["data"]) == 1
            assert body["data"][0]["user_id"] == "user_2"

    def test_list_audit_logs_with_target_id_filter(self, admin_client, sample_audit_logs):
        """Filtering by target_id query parameter works."""
        filtered = [log for log in sample_audit_logs if log.target_id == "ds_001"]

        async def mock_list_all(self, dynamodb, **kwargs):
            assert kwargs.get("target_id") == "ds_001"
            return filtered
        with patch.object(audit_log_repository.AuditLogRepository, 'list_all', mock_list_all):
            response = admin_client.get("/api/audit-logs?target_id=ds_001")
            assert response.status_code == 200
            body = response.json()
            assert len(body["data"]) == 1
            assert body["data"][0]["target_id"] == "ds_001"

    def test_list_audit_logs_with_date_range(self, admin_client, sample_audit_logs):
        """Filtering by start_date and end_date query parameters works."""
        async def mock_list_all(self, dynamodb, **kwargs):
            assert kwargs.get("start_date") is not None
            assert kwargs.get("end_date") is not None
            return sample_audit_logs
        with patch.object(audit_log_repository.AuditLogRepository, 'list_all', mock_list_all):
            response = admin_client.get(
                "/api/audit-logs?start_date=2025-01-01T00:00:00Z&end_date=2025-12-31T23:59:59Z"
            )
            assert response.status_code == 200
            body = response.json()
            assert "data" in body
            assert "pagination" in body

    def test_list_audit_logs_pagination(self, admin_client):
        """Pagination with limit and offset works correctly."""
        now = datetime.now(timezone.utc)
        all_logs = [
            AuditLog(
                log_id=f"log_{i:03d}",
                timestamp=now,
                event_type=EventType.USER_LOGIN,
                user_id="user_1",
                target_type="user",
                target_id="user_1",
                details={},
            )
            for i in range(5)
        ]

        async def mock_list_all(self, dynamodb, **kwargs):
            return all_logs
        with patch.object(audit_log_repository.AuditLogRepository, 'list_all', mock_list_all):
            response = admin_client.get("/api/audit-logs?limit=2&offset=1")
            assert response.status_code == 200
            body = response.json()
            assert len(body["data"]) == 2
            assert body["pagination"]["total"] == 5
            assert body["pagination"]["limit"] == 2
            assert body["pagination"]["offset"] == 1
            assert body["pagination"]["has_next"] is True
