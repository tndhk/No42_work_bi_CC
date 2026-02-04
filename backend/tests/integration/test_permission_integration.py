"""Integration tests for permission system with real DynamoDB (moto).

Tests complex permission scenarios involving multiple services and repositories
working together against moto-mocked DynamoDB tables.
"""
import asyncio
import pytest
from datetime import datetime, timezone

from app.models.dashboard import Dashboard
from app.models.dashboard_share import Permission, SharedToType
from app.services.permission_service import PermissionService
from app.repositories.dashboard_share_repository import DashboardShareRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.group_member_repository import GroupMemberRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dashboard(dashboard_id: str, owner_id: str) -> Dashboard:
    """Create a Dashboard model instance for testing."""
    now = datetime.now(timezone.utc)
    return Dashboard(
        id=dashboard_id,
        name=f"Dashboard {dashboard_id}",
        owner_id=owner_id,
        created_at=now,
        updated_at=now,
    )


def _make_share_data(
    share_id: str,
    dashboard_id: str,
    shared_to_type: SharedToType,
    shared_to_id: str,
    permission: Permission,
    shared_by: str,
) -> dict:
    """Build a dict suitable for DashboardShareRepository.create()."""
    return {
        "id": share_id,
        "dashboard_id": dashboard_id,
        "shared_to_type": shared_to_type,
        "shared_to_id": shared_to_id,
        "permission": permission,
        "shared_by": shared_by,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dynamodb(dynamodb_tables):
    """Extract the DynamoDB resource from the dynamodb_tables fixture."""
    _tables, dynamodb_resource = dynamodb_tables
    return dynamodb_resource


@pytest.fixture
def permission_service() -> PermissionService:
    return PermissionService()


@pytest.fixture
def share_repo() -> DashboardShareRepository:
    return DashboardShareRepository()


@pytest.fixture
def group_repo() -> GroupRepository:
    return GroupRepository()


@pytest.fixture
def member_repo() -> GroupMemberRepository:
    return GroupMemberRepository()


# ---------------------------------------------------------------------------
# Test 1: Direct share + group share -- highest permission wins
# ---------------------------------------------------------------------------

class TestDirectAndGroupShareHighestPermission:
    """user-B has viewer via direct share and editor via group share.

    Expected: get_user_permission returns editor (the higher of the two).
    """

    def test_user_gets_highest_of_direct_and_group_permissions(
        self, dynamodb, permission_service, share_repo, group_repo, member_repo
    ):
        async def _run():
            dashboard = _make_dashboard("dash-1", "user-A")

            # Direct share: user-B -> viewer
            await share_repo.create(
                _make_share_data(
                    "share-1", "dash-1",
                    SharedToType.USER, "user-B",
                    Permission.VIEWER, "user-A",
                ),
                dynamodb,
            )

            # Group share: group-1 -> editor
            await group_repo.create({"id": "group-1", "name": "Group 1"}, dynamodb)
            await share_repo.create(
                _make_share_data(
                    "share-2", "dash-1",
                    SharedToType.GROUP, "group-1",
                    Permission.EDITOR, "user-A",
                ),
                dynamodb,
            )

            # user-B is a member of group-1
            await member_repo.add_member("group-1", "user-B", dynamodb)

            # Assert highest permission
            perm = await permission_service.get_user_permission(dashboard, "user-B", dynamodb)
            assert perm == Permission.EDITOR

            # Also verify via check_permission
            assert await permission_service.check_permission(
                dashboard, "user-B", Permission.EDITOR, dynamodb
            ) is True
            assert await permission_service.check_permission(
                dashboard, "user-B", Permission.OWNER, dynamodb
            ) is False

        asyncio.get_event_loop().run_until_complete(_run())


# ---------------------------------------------------------------------------
# Test 2: Multiple group shares -- permission aggregation
# ---------------------------------------------------------------------------

class TestMultipleGroupPermissionAggregation:
    """user-C belongs to group-1 (viewer) and group-2 (editor).

    Expected: get_user_permission returns editor.
    """

    def test_highest_group_permission_is_selected(
        self, dynamodb, permission_service, share_repo, group_repo, member_repo
    ):
        async def _run():
            dashboard = _make_dashboard("dash-2", "user-A")

            # Create groups
            await group_repo.create({"id": "group-1", "name": "Group 1"}, dynamodb)
            await group_repo.create({"id": "group-2", "name": "Group 2"}, dynamodb)

            # Share dashboard to groups
            await share_repo.create(
                _make_share_data(
                    "share-10", "dash-2",
                    SharedToType.GROUP, "group-1",
                    Permission.VIEWER, "user-A",
                ),
                dynamodb,
            )
            await share_repo.create(
                _make_share_data(
                    "share-11", "dash-2",
                    SharedToType.GROUP, "group-2",
                    Permission.EDITOR, "user-A",
                ),
                dynamodb,
            )

            # user-C is in both groups
            await member_repo.add_member("group-1", "user-C", dynamodb)
            await member_repo.add_member("group-2", "user-C", dynamodb)

            perm = await permission_service.get_user_permission(dashboard, "user-C", dynamodb)
            assert perm == Permission.EDITOR

        asyncio.get_event_loop().run_until_complete(_run())


# ---------------------------------------------------------------------------
# Test 3: No permission -- access denied
# ---------------------------------------------------------------------------

class TestNoPermissionAccessDenied:
    """user-D has no shares and no group memberships.

    Expected: get_user_permission returns None.
    """

    def test_user_without_any_share_gets_none(
        self, dynamodb, permission_service, share_repo, group_repo, member_repo
    ):
        async def _run():
            dashboard = _make_dashboard("dash-3", "user-A")

            # Create some shares for other users to ensure user-D is excluded
            await share_repo.create(
                _make_share_data(
                    "share-20", "dash-3",
                    SharedToType.USER, "user-B",
                    Permission.EDITOR, "user-A",
                ),
                dynamodb,
            )

            perm = await permission_service.get_user_permission(dashboard, "user-D", dynamodb)
            assert perm is None

            # check_permission should return False
            assert await permission_service.check_permission(
                dashboard, "user-D", Permission.VIEWER, dynamodb
            ) is False

        asyncio.get_event_loop().run_until_complete(_run())

    def test_assert_permission_raises_403_for_no_access(
        self, dynamodb, permission_service
    ):
        from fastapi import HTTPException

        async def _run():
            dashboard = _make_dashboard("dash-3b", "user-A")

            with pytest.raises(HTTPException) as exc_info:
                await permission_service.assert_permission(
                    dashboard, "user-D", Permission.VIEWER, dynamodb
                )
            assert exc_info.value.status_code == 403

        asyncio.get_event_loop().run_until_complete(_run())


# ---------------------------------------------------------------------------
# Test 4: Owner always gets owner permission
# ---------------------------------------------------------------------------

class TestOwnerAlwaysGetsOwnerPermission:
    """Even if owner has a conflicting direct share (viewer), owner_id check wins.

    Expected: get_user_permission returns owner.
    """

    def test_owner_overrides_direct_viewer_share(
        self, dynamodb, permission_service, share_repo
    ):
        async def _run():
            dashboard = _make_dashboard("dash-4", "user-A")

            # Contradictory direct share: owner with viewer
            await share_repo.create(
                _make_share_data(
                    "share-30", "dash-4",
                    SharedToType.USER, "user-A",
                    Permission.VIEWER, "user-A",
                ),
                dynamodb,
            )

            perm = await permission_service.get_user_permission(dashboard, "user-A", dynamodb)
            assert perm == Permission.OWNER

            # Owner should pass all permission checks
            assert await permission_service.check_permission(
                dashboard, "user-A", Permission.OWNER, dynamodb
            ) is True
            assert await permission_service.check_permission(
                dashboard, "user-A", Permission.EDITOR, dynamodb
            ) is True
            assert await permission_service.check_permission(
                dashboard, "user-A", Permission.VIEWER, dynamodb
            ) is True

        asyncio.get_event_loop().run_until_complete(_run())


# ---------------------------------------------------------------------------
# Test 5: Group member removal revokes group-based permission
# ---------------------------------------------------------------------------

class TestGroupMemberRemovalRevokesPermission:
    """After removing user-E from group-1, the group-based editor permission is gone.

    Expected: permission drops from editor to None.
    """

    def test_removing_member_revokes_group_permission(
        self, dynamodb, permission_service, share_repo, group_repo, member_repo
    ):
        async def _run():
            dashboard = _make_dashboard("dash-5", "user-A")

            # Group share
            await group_repo.create({"id": "group-1", "name": "Group 1"}, dynamodb)
            await share_repo.create(
                _make_share_data(
                    "share-40", "dash-5",
                    SharedToType.GROUP, "group-1",
                    Permission.EDITOR, "user-A",
                ),
                dynamodb,
            )

            # user-E joins group-1
            await member_repo.add_member("group-1", "user-E", dynamodb)

            # Confirm permission
            perm_before = await permission_service.get_user_permission(
                dashboard, "user-E", dynamodb
            )
            assert perm_before == Permission.EDITOR

            # Remove user-E from group-1
            await member_repo.remove_member("group-1", "user-E", dynamodb)

            # Permission should now be None
            perm_after = await permission_service.get_user_permission(
                dashboard, "user-E", dynamodb
            )
            assert perm_after is None

        asyncio.get_event_loop().run_until_complete(_run())

    def test_removing_member_preserves_direct_share(
        self, dynamodb, permission_service, share_repo, group_repo, member_repo
    ):
        """Even after group removal, a direct share remains."""

        async def _run():
            dashboard = _make_dashboard("dash-5b", "user-A")

            # Direct share: user-F -> viewer
            await share_repo.create(
                _make_share_data(
                    "share-50", "dash-5b",
                    SharedToType.USER, "user-F",
                    Permission.VIEWER, "user-A",
                ),
                dynamodb,
            )

            # Group share: group-2 -> editor
            await group_repo.create({"id": "group-2", "name": "Group 2"}, dynamodb)
            await share_repo.create(
                _make_share_data(
                    "share-51", "dash-5b",
                    SharedToType.GROUP, "group-2",
                    Permission.EDITOR, "user-A",
                ),
                dynamodb,
            )

            # user-F is in group-2
            await member_repo.add_member("group-2", "user-F", dynamodb)

            # Before removal: editor (highest)
            perm_before = await permission_service.get_user_permission(
                dashboard, "user-F", dynamodb
            )
            assert perm_before == Permission.EDITOR

            # Remove from group
            await member_repo.remove_member("group-2", "user-F", dynamodb)

            # After removal: viewer (direct share remains)
            perm_after = await permission_service.get_user_permission(
                dashboard, "user-F", dynamodb
            )
            assert perm_after == Permission.VIEWER

        asyncio.get_event_loop().run_until_complete(_run())
