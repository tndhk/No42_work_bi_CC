"""Permission service for dashboard access control."""
from typing import Any, Optional
from fastapi import HTTPException, status

from app.models.dashboard import Dashboard
from app.models.dashboard_share import Permission, SharedToType
from app.repositories.dashboard_share_repository import DashboardShareRepository
from app.repositories.group_member_repository import GroupMemberRepository

PERMISSION_LEVELS = {
    Permission.VIEWER: 1,
    Permission.EDITOR: 2,
    Permission.OWNER: 3,
}


class PermissionService:
    """Service for managing dashboard permissions."""

    async def get_user_permission(
        self,
        dashboard: Dashboard,
        user_id: str,
        dynamodb: Any,
    ) -> Optional[Permission]:
        """Get the highest permission level for a user on a dashboard.

        1. Check if user is the owner
        2. Check direct user shares
        3. Check group shares via group membership
        4. Return the highest permission level found

        Args:
            dashboard: Dashboard instance
            user_id: User ID to check
            dynamodb: DynamoDB resource

        Returns:
            Highest Permission level, or None if no access
        """
        # 1. Owner check
        if dashboard.owner_id == user_id:
            return Permission.OWNER

        # 2-3. Get all shares for this dashboard
        share_repo = DashboardShareRepository()
        all_shares = await share_repo.list_by_dashboard(dashboard.id, dynamodb)

        # Get user's groups for group share checking
        member_repo = GroupMemberRepository()
        user_groups = await member_repo.list_groups_for_user(user_id, dynamodb)
        user_group_set = set(user_groups)

        highest_level = 0
        highest_permission = None

        for share in all_shares:
            if (share.shared_to_type == SharedToType.USER and share.shared_to_id == user_id) or \
               (share.shared_to_type == SharedToType.GROUP and share.shared_to_id in user_group_set):
                level = PERMISSION_LEVELS.get(share.permission, 0)
                if level > highest_level:
                    highest_level = level
                    highest_permission = share.permission

        return highest_permission

    async def check_permission(
        self,
        dashboard: Dashboard,
        user_id: str,
        required: Permission,
        dynamodb: Any,
    ) -> bool:
        """Check if user has at least the required permission level."""
        user_perm = await self.get_user_permission(dashboard, user_id, dynamodb)
        if user_perm is None:
            return False
        return PERMISSION_LEVELS.get(user_perm, 0) >= PERMISSION_LEVELS.get(required, 0)

    async def assert_permission(
        self,
        dashboard: Dashboard,
        user_id: str,
        required: Permission,
        dynamodb: Any,
    ) -> None:
        """Assert user has required permission, raise 403 if not."""
        has_perm = await self.check_permission(dashboard, user_id, required, dynamodb)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required.value} permission or higher",
            )
