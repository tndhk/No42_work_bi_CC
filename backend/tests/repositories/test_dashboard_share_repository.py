"""Tests for DashboardShareRepository."""
import pytest
from datetime import datetime
from typing import Any


@pytest.mark.asyncio
class TestDashboardShareRepository:
    """Test suite for DashboardShareRepository CRUD operations."""

    def _create_share_data(
        self,
        share_id: str = "share_1",
        dashboard_id: str = "dash_1",
        shared_to_type: str = "user",
        shared_to_id: str = "user_2",
        permission: str = "viewer",
        shared_by: str = "user_1",
    ) -> dict[str, Any]:
        """Helper to create share data dict."""
        return {
            "id": share_id,
            "dashboard_id": dashboard_id,
            "shared_to_type": shared_to_type,
            "shared_to_id": shared_to_id,
            "permission": permission,
            "shared_by": shared_by,
        }

    async def test_create_share(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating a dashboard share."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        data = self._create_share_data()
        share = await repo.create(data, dynamodb)

        assert share.id == "share_1"
        assert share.dashboard_id == "dash_1"
        assert share.shared_to_type == "user"
        assert share.shared_to_id == "user_2"
        assert share.permission == "viewer"
        assert share.shared_by == "user_1"
        assert isinstance(share.created_at, datetime)

    async def test_get_by_id(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test getting a share by ID."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        await repo.create(self._create_share_data(), dynamodb)
        share = await repo.get_by_id("share_1", dynamodb)

        assert share is not None
        assert share.id == "share_1"
        assert share.dashboard_id == "dash_1"
        assert share.permission == "viewer"

    async def test_get_by_id_nonexistent(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test getting a non-existent share returns None."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        result = await repo.get_by_id("nonexistent", dynamodb)
        assert result is None

    async def test_list_by_dashboard(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing shares for a dashboard using SharesByDashboard GSI."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        # Create two shares for dash_1
        await repo.create(
            self._create_share_data("share_1", "dash_1", shared_to_id="user_2"), dynamodb
        )
        await repo.create(
            self._create_share_data("share_2", "dash_1", shared_to_id="user_3"), dynamodb
        )
        # Create one share for dash_2
        await repo.create(
            self._create_share_data("share_3", "dash_2"), dynamodb
        )

        shares = await repo.list_by_dashboard("dash_1", dynamodb)
        assert len(shares) == 2
        assert all(s.dashboard_id == "dash_1" for s in shares)
        assert not any(s.id == "share_3" for s in shares)

    async def test_list_by_dashboard_empty(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing shares for a dashboard with no shares returns empty list."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        shares = await repo.list_by_dashboard("dash_empty", dynamodb)
        assert shares == []

    async def test_list_by_target(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing shares for a target user using SharesByTarget GSI."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        # Create two shares targeting user_2
        await repo.create(
            self._create_share_data("share_1", "dash_1", shared_to_id="user_2"), dynamodb
        )
        await repo.create(
            self._create_share_data("share_2", "dash_2", shared_to_id="user_2"), dynamodb
        )
        # Create one share targeting user_3
        await repo.create(
            self._create_share_data("share_3", "dash_3", shared_to_id="user_3"), dynamodb
        )

        shares = await repo.list_by_target("user_2", dynamodb)
        assert len(shares) == 2
        assert all(s.shared_to_id == "user_2" for s in shares)

    async def test_list_by_target_empty(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing shares for a target with no shares returns empty list."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        shares = await repo.list_by_target("user_nobody", dynamodb)
        assert shares == []

    async def test_find_share(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test finding a specific share by dashboard + shared_to_type + shared_to_id."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        await repo.create(
            self._create_share_data("share_1", "dash_1", "user", "user_2"), dynamodb
        )

        share = await repo.find_share("dash_1", "user", "user_2", dynamodb)
        assert share is not None
        assert share.id == "share_1"
        assert share.dashboard_id == "dash_1"
        assert share.shared_to_type == "user"
        assert share.shared_to_id == "user_2"

    async def test_find_share_not_found(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test finding a non-existent share returns None."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        share = await repo.find_share("dash_1", "user", "user_999", dynamodb)
        assert share is None

    async def test_find_share_distinguishes_type(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that find_share distinguishes between user and group shared_to_type."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        await repo.create(
            self._create_share_data("share_1", "dash_1", "user", "target_1"), dynamodb
        )
        await repo.create(
            self._create_share_data("share_2", "dash_1", "group", "target_1"), dynamodb
        )

        user_share = await repo.find_share("dash_1", "user", "target_1", dynamodb)
        assert user_share is not None
        assert user_share.id == "share_1"

        group_share = await repo.find_share("dash_1", "group", "target_1", dynamodb)
        assert group_share is not None
        assert group_share.id == "share_2"

    async def test_delete_share(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a share."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        await repo.create(self._create_share_data(), dynamodb)
        await repo.delete("share_1", dynamodb)

        share = await repo.get_by_id("share_1", dynamodb)
        assert share is None

    async def test_delete_nonexistent_no_error(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a non-existent share does not raise an error."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        # Should not raise
        await repo.delete("nonexistent", dynamodb)

    async def test_create_with_different_permissions(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating shares with different permission levels."""
        from app.repositories.dashboard_share_repository import DashboardShareRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardShareRepository()

        for perm in ["owner", "editor", "viewer"]:
            share = await repo.create(
                self._create_share_data(f"share_{perm}", permission=perm), dynamodb
            )
            assert share.permission == perm
