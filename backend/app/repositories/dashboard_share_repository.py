"""DashboardShare repository for DynamoDB operations."""
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings
from app.models.dashboard_share import DashboardShare
from app.repositories.base import BaseRepository


class DashboardShareRepository(BaseRepository[DashboardShare]):
    """Repository for DashboardShare entity operations.

    Provides CRUD operations and query methods using GSIs:
    - SharesByDashboard: Query shares by dashboard_id
    - SharesByTarget: Query shares by shared_to_id
    """

    def __init__(self) -> None:
        """Initialize DashboardShareRepository with dashboard_shares table configuration."""
        super().__init__(
            table_name=f"{settings.dynamodb_table_prefix}dashboard_shares",
            pk_name='shareId',
            model=DashboardShare
        )

    async def create(self, data: dict[str, Any], dynamodb: Any) -> DashboardShare:
        """Create a new dashboard share with automatic created_at timestamp.

        Overrides BaseRepository.create() because DashboardShare does not have
        an updated_at field (shares are immutable once created, only deletable).

        Args:
            data: Item data dictionary (snake_case keys)
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            Created DashboardShare instance
        """
        item_data = {**data}

        now = datetime.now(timezone.utc)
        item_data['created_at'] = now

        dynamodb_item = self._to_dynamodb_item(item_data)
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)
        await self._execute_db_operation(table.put_item(Item=dynamodb_item))

        return self.model(**item_data)

    async def list_by_dashboard(self, dashboard_id: str, dynamodb: Any) -> list[DashboardShare]:
        """List all shares for a dashboard using SharesByDashboard GSI.

        Args:
            dashboard_id: Dashboard ID to filter by
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            List of DashboardShare instances for the given dashboard
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(
            table.query(
                IndexName='SharesByDashboard',
                KeyConditionExpression='dashboardId = :did',
                ExpressionAttributeValues={':did': dashboard_id}
            )
        )

        items = response.get('Items', [])
        if not items:
            return []

        return [
            self.model(**self._from_dynamodb_item(item))
            for item in items
        ]

    async def list_by_target(self, shared_to_id: str, dynamodb: Any) -> list[DashboardShare]:
        """List all shares for a target (user or group) using SharesByTarget GSI.

        Args:
            shared_to_id: Target user or group ID
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            List of DashboardShare instances for the given target
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(
            table.query(
                IndexName='SharesByTarget',
                KeyConditionExpression='sharedToId = :stid',
                ExpressionAttributeValues={':stid': shared_to_id}
            )
        )

        items = response.get('Items', [])
        if not items:
            return []

        return [
            self.model(**self._from_dynamodb_item(item))
            for item in items
        ]

    async def find_share(
        self,
        dashboard_id: str,
        shared_to_type: str,
        shared_to_id: str,
        dynamodb: Any
    ) -> Optional[DashboardShare]:
        """Find a specific share by dashboard + shared_to_type + shared_to_id.

        Uses SharesByDashboard GSI to query by dashboard_id, then filters
        in-memory by shared_to_type and shared_to_id.

        Args:
            dashboard_id: Dashboard ID
            shared_to_type: "user" or "group"
            shared_to_id: Target user or group ID
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            DashboardShare if found, None otherwise
        """
        shares = await self.list_by_dashboard(dashboard_id, dynamodb)
        for share in shares:
            if share.shared_to_type == shared_to_type and share.shared_to_id == shared_to_id:
                return share
        return None
