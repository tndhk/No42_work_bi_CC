"""Tests for AuditLog model."""
import pytest
from datetime import datetime, timezone
from app.models.audit_log import AuditLog, EventType


class TestEventType:
    """Tests for EventType enum."""

    def test_all_event_types_exist(self):
        """All 13 event types should be defined."""
        expected = [
            "USER_LOGIN", "USER_LOGOUT", "USER_LOGIN_FAILED",
            "DASHBOARD_SHARE_ADDED", "DASHBOARD_SHARE_REMOVED", "DASHBOARD_SHARE_UPDATED",
            "DATASET_CREATED", "DATASET_IMPORTED", "DATASET_DELETED",
            "TRANSFORM_EXECUTED", "TRANSFORM_FAILED",
            "CARD_EXECUTION_FAILED",
            "CHATBOT_QUERY",
        ]
        for name in expected:
            assert hasattr(EventType, name), f"EventType.{name} should exist"

    def test_event_type_count(self):
        """Exactly 13 event types."""
        assert len(EventType) == 13

    def test_chatbot_query_event_type_value(self):
        """CHATBOT_QUERY value should match its name."""
        assert EventType.CHATBOT_QUERY.value == "CHATBOT_QUERY"

    def test_event_type_values(self):
        """Values should match names (lowercase convention)."""
        assert EventType.USER_LOGIN.value == "USER_LOGIN"
        assert EventType.CARD_EXECUTION_FAILED.value == "CARD_EXECUTION_FAILED"


class TestAuditLog:
    """Tests for AuditLog model."""

    def test_create_audit_log(self):
        """Test creating an audit log entry with all fields."""
        now = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        log = AuditLog(
            log_id="log_abc123def456",
            timestamp=now,
            event_type=EventType.USER_LOGIN,
            user_id="user-001",
            target_type="user",
            target_id="user-001",
            details={"ip": "127.0.0.1"},
            request_id="req-001",
        )
        assert log.log_id == "log_abc123def456"
        assert log.timestamp == now
        assert log.event_type == EventType.USER_LOGIN
        assert log.user_id == "user-001"
        assert log.target_type == "user"
        assert log.target_id == "user-001"
        assert log.details == {"ip": "127.0.0.1"}
        assert log.request_id == "req-001"

    def test_create_audit_log_minimal(self):
        """Test creating an audit log with only required fields."""
        now = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        log = AuditLog(
            log_id="log_abc123def456",
            timestamp=now,
            event_type=EventType.DATASET_CREATED,
            user_id="user-002",
            target_type="dataset",
            target_id="ds-001",
        )
        assert log.details == {}
        assert log.request_id is None

    def test_audit_log_from_attributes(self):
        """Test ConfigDict(from_attributes=True)."""
        now = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        log = AuditLog.model_validate({
            "log_id": "log_test123",
            "timestamp": now,
            "event_type": EventType.USER_LOGOUT,
            "user_id": "user-003",
            "target_type": "user",
            "target_id": "user-003",
        })
        assert log.log_id == "log_test123"

    def test_audit_log_event_type_from_string(self):
        """Test that event_type can be set from string value."""
        now = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        log = AuditLog(
            log_id="log_test456",
            timestamp=now,
            event_type="USER_LOGIN",
            user_id="user-004",
            target_type="user",
            target_id="user-004",
        )
        assert log.event_type == EventType.USER_LOGIN
