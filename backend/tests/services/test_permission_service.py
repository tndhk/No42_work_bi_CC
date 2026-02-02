"""Tests for PermissionService."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.services.permission_service import PermissionService
from app.models.dashboard import Dashboard
from app.models.dashboard_share import DashboardShare, Permission, SharedToType


@pytest.fixture
def service():
    return PermissionService()


@pytest.fixture
def mock_dynamodb():
    return MagicMock()


@pytest.fixture
def sample_dashboard():
    return Dashboard(
        id="dash_1", name="Test", owner_id="user_owner",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_share(shared_to_type, shared_to_id, permission):
    return DashboardShare(
        id="share_x", dashboard_id="dash_1",
        shared_to_type=shared_to_type,
        shared_to_id=shared_to_id,
        permission=permission,
        shared_by="user_owner",
        created_at=datetime.now(timezone.utc),
    )


class TestGetUserPermission:
    def test_owner_returns_owner(self, service, sample_dashboard, mock_dynamodb):
        result = asyncio.get_event_loop().run_until_complete(
            service.get_user_permission(sample_dashboard, "user_owner", mock_dynamodb)
        )
        assert result == Permission.OWNER

    def test_direct_user_share(self, service, sample_dashboard, mock_dynamodb):
        user_share = make_share(SharedToType.USER, "user_2", Permission.EDITOR)
        with patch('app.services.permission_service.DashboardShareRepository') as MockShareRepo, \
             patch('app.services.permission_service.GroupMemberRepository') as MockMemberRepo:
            mock_share_instance = MockShareRepo.return_value
            mock_share_instance.list_by_dashboard = AsyncMock(return_value=[user_share])
            mock_member_instance = MockMemberRepo.return_value
            mock_member_instance.list_groups_for_user = AsyncMock(return_value=[])

            result = asyncio.get_event_loop().run_until_complete(
                service.get_user_permission(sample_dashboard, "user_2", mock_dynamodb)
            )
            assert result == Permission.EDITOR

    def test_group_share(self, service, sample_dashboard, mock_dynamodb):
        group_share = make_share(SharedToType.GROUP, "group_1", Permission.VIEWER)
        with patch('app.services.permission_service.DashboardShareRepository') as MockShareRepo, \
             patch('app.services.permission_service.GroupMemberRepository') as MockMemberRepo:
            mock_share_instance = MockShareRepo.return_value
            mock_share_instance.list_by_dashboard = AsyncMock(return_value=[group_share])
            mock_member_instance = MockMemberRepo.return_value
            mock_member_instance.list_groups_for_user = AsyncMock(return_value=["group_1"])

            result = asyncio.get_event_loop().run_until_complete(
                service.get_user_permission(sample_dashboard, "user_3", mock_dynamodb)
            )
            assert result == Permission.VIEWER

    def test_no_permission(self, service, sample_dashboard, mock_dynamodb):
        with patch('app.services.permission_service.DashboardShareRepository') as MockShareRepo, \
             patch('app.services.permission_service.GroupMemberRepository') as MockMemberRepo:
            mock_share_instance = MockShareRepo.return_value
            mock_share_instance.list_by_dashboard = AsyncMock(return_value=[])
            mock_member_instance = MockMemberRepo.return_value
            mock_member_instance.list_groups_for_user = AsyncMock(return_value=[])

            result = asyncio.get_event_loop().run_until_complete(
                service.get_user_permission(sample_dashboard, "user_nobody", mock_dynamodb)
            )
            assert result is None

    def test_highest_permission_wins(self, service, sample_dashboard, mock_dynamodb):
        """Direct viewer share + group editor share -> editor wins."""
        user_share = make_share(SharedToType.USER, "user_2", Permission.VIEWER)
        group_share = make_share(SharedToType.GROUP, "group_1", Permission.EDITOR)
        with patch('app.services.permission_service.DashboardShareRepository') as MockShareRepo, \
             patch('app.services.permission_service.GroupMemberRepository') as MockMemberRepo:
            mock_share_instance = MockShareRepo.return_value
            mock_share_instance.list_by_dashboard = AsyncMock(return_value=[user_share, group_share])
            mock_member_instance = MockMemberRepo.return_value
            mock_member_instance.list_groups_for_user = AsyncMock(return_value=["group_1"])

            result = asyncio.get_event_loop().run_until_complete(
                service.get_user_permission(sample_dashboard, "user_2", mock_dynamodb)
            )
            assert result == Permission.EDITOR


class TestCheckPermission:
    def test_check_sufficient(self, service, sample_dashboard, mock_dynamodb):
        with patch.object(service, 'get_user_permission', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = Permission.EDITOR
            result = asyncio.get_event_loop().run_until_complete(
                service.check_permission(sample_dashboard, "user_2", Permission.VIEWER, mock_dynamodb)
            )
            assert result is True

    def test_check_insufficient(self, service, sample_dashboard, mock_dynamodb):
        with patch.object(service, 'get_user_permission', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = Permission.VIEWER
            result = asyncio.get_event_loop().run_until_complete(
                service.check_permission(sample_dashboard, "user_2", Permission.EDITOR, mock_dynamodb)
            )
            assert result is False

    def test_check_no_permission(self, service, sample_dashboard, mock_dynamodb):
        with patch.object(service, 'get_user_permission', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = asyncio.get_event_loop().run_until_complete(
                service.check_permission(sample_dashboard, "user_2", Permission.VIEWER, mock_dynamodb)
            )
            assert result is False


class TestAssertPermission:
    def test_assert_passes(self, service, sample_dashboard, mock_dynamodb):
        with patch.object(service, 'check_permission', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = True
            # Should not raise
            asyncio.get_event_loop().run_until_complete(
                service.assert_permission(sample_dashboard, "user_2", Permission.VIEWER, mock_dynamodb)
            )

    def test_assert_raises_403(self, service, sample_dashboard, mock_dynamodb):
        from fastapi import HTTPException
        with patch.object(service, 'check_permission', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = False
            with pytest.raises(HTTPException) as exc_info:
                asyncio.get_event_loop().run_until_complete(
                    service.assert_permission(sample_dashboard, "user_2", Permission.EDITOR, mock_dynamodb)
                )
            assert exc_info.value.status_code == 403
