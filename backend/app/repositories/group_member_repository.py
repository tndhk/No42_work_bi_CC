"""GroupMember repository for DynamoDB operations."""
from datetime import datetime, timezone
from typing import Any
import inspect

from app.core.config import settings
from app.models.group import GroupMember


class GroupMemberRepository:
    """Repository for GroupMember entity operations.

    Uses composite key (groupId + userId) so does not extend BaseRepository.
    """

    def __init__(self) -> None:
        self.table_name = f"{settings.dynamodb_table_prefix}group_members"

    async def _execute_db_operation(self, operation: Any) -> Any:
        if inspect.iscoroutine(operation):
            return await operation
        return operation

    async def _get_table(self, dynamodb: Any) -> Any:
        table_result = dynamodb.Table(self.table_name)
        return await self._execute_db_operation(table_result)

    async def add_member(self, group_id: str, user_id: str, dynamodb: Any) -> GroupMember:
        """Add a member to a group.

        Args:
            group_id: Group ID
            user_id: User ID
            dynamodb: DynamoDB resource

        Returns:
            GroupMember instance
        """
        now = datetime.now(timezone.utc)
        table = await self._get_table(dynamodb)

        item = {
            'groupId': group_id,
            'userId': user_id,
            'addedAt': int(now.timestamp()),
        }

        await self._execute_db_operation(table.put_item(Item=item))

        return GroupMember(group_id=group_id, user_id=user_id, added_at=now)

    async def remove_member(self, group_id: str, user_id: str, dynamodb: Any) -> None:
        """Remove a member from a group."""
        table = await self._get_table(dynamodb)
        await self._execute_db_operation(
            table.delete_item(Key={'groupId': group_id, 'userId': user_id})
        )

    async def list_members(self, group_id: str, dynamodb: Any) -> list[GroupMember]:
        """List all members of a group."""
        table = await self._get_table(dynamodb)
        response = await self._execute_db_operation(
            table.query(
                KeyConditionExpression='groupId = :gid',
                ExpressionAttributeValues={':gid': group_id}
            )
        )

        return [
            GroupMember(
                group_id=item['groupId'],
                user_id=item['userId'],
                added_at=datetime.fromtimestamp(int(item['addedAt']), tz=timezone.utc),
            )
            for item in response.get('Items', [])
        ]

    async def is_member(self, group_id: str, user_id: str, dynamodb: Any) -> bool:
        """Check if a user is a member of a group."""
        table = await self._get_table(dynamodb)
        response = await self._execute_db_operation(
            table.get_item(Key={'groupId': group_id, 'userId': user_id})
        )
        return 'Item' in response

    async def list_groups_for_user(self, user_id: str, dynamodb: Any) -> list[str]:
        """List all group IDs for a user using MembersByUser GSI."""
        table = await self._get_table(dynamodb)
        response = await self._execute_db_operation(
            table.query(
                IndexName='MembersByUser',
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
        )

        return [item['groupId'] for item in response.get('Items', [])]
