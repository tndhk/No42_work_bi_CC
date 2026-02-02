"""Tests for DashboardShare models."""
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.models.dashboard_share import (
    Permission,
    SharedToType,
    DashboardShare,
    DashboardShareCreate,
    DashboardShareUpdate,
)


class TestPermission:
    """Test Permission enum."""

    def test_permission_values(self):
        assert Permission.OWNER == "owner"
        assert Permission.EDITOR == "editor"
        assert Permission.VIEWER == "viewer"

    def test_permission_is_string(self):
        assert isinstance(Permission.OWNER, str)
        assert isinstance(Permission.EDITOR, str)
        assert isinstance(Permission.VIEWER, str)


class TestSharedToType:
    """Test SharedToType enum."""

    def test_shared_to_type_values(self):
        assert SharedToType.USER == "user"
        assert SharedToType.GROUP == "group"


class TestDashboardShare:
    """Test DashboardShare model."""

    def test_dashboard_share_valid(self):
        share = DashboardShare(
            id="share_abc123",
            dashboard_id="dash_123",
            shared_to_type=SharedToType.USER,
            shared_to_id="user_456",
            permission=Permission.VIEWER,
            shared_by="user_123",
            created_at=datetime.utcnow(),
        )
        assert share.id == "share_abc123"
        assert share.dashboard_id == "dash_123"
        assert share.shared_to_type == SharedToType.USER
        assert share.shared_to_id == "user_456"
        assert share.permission == Permission.VIEWER
        assert share.shared_by == "user_123"

    def test_dashboard_share_group_type(self):
        share = DashboardShare(
            id="share_abc456",
            dashboard_id="dash_123",
            shared_to_type=SharedToType.GROUP,
            shared_to_id="group_abc123",
            permission=Permission.EDITOR,
            shared_by="user_123",
            created_at=datetime.utcnow(),
        )
        assert share.shared_to_type == SharedToType.GROUP

    def test_dashboard_share_serialization(self):
        share = DashboardShare(
            id="share_abc123",
            dashboard_id="dash_123",
            shared_to_type=SharedToType.USER,
            shared_to_id="user_456",
            permission=Permission.VIEWER,
            shared_by="user_123",
            created_at=datetime.utcnow(),
        )
        d = share.model_dump()
        assert d["id"] == "share_abc123"
        assert d["shared_to_type"] == "user"
        assert d["permission"] == "viewer"

    def test_dashboard_share_missing_fields_fails(self):
        with pytest.raises(ValidationError):
            DashboardShare(id="share_abc123")


class TestDashboardShareCreate:
    """Test DashboardShareCreate model."""

    def test_create_valid(self):
        sc = DashboardShareCreate(
            shared_to_type=SharedToType.USER,
            shared_to_id="user_456",
            permission=Permission.VIEWER,
        )
        assert sc.shared_to_type == SharedToType.USER
        assert sc.shared_to_id == "user_456"
        assert sc.permission == Permission.VIEWER

    def test_create_group_share(self):
        sc = DashboardShareCreate(
            shared_to_type=SharedToType.GROUP,
            shared_to_id="group_abc123",
            permission=Permission.EDITOR,
        )
        assert sc.shared_to_type == SharedToType.GROUP

    def test_create_missing_fields_fails(self):
        with pytest.raises(ValidationError):
            DashboardShareCreate()

    def test_create_invalid_permission_fails(self):
        with pytest.raises(ValidationError):
            DashboardShareCreate(
                shared_to_type=SharedToType.USER,
                shared_to_id="user_456",
                permission="invalid",
            )


class TestDashboardShareUpdate:
    """Test DashboardShareUpdate model."""

    def test_update_permission(self):
        su = DashboardShareUpdate(permission=Permission.EDITOR)
        assert su.permission == Permission.EDITOR

    def test_update_invalid_permission_fails(self):
        with pytest.raises(ValidationError):
            DashboardShareUpdate(permission="invalid")
