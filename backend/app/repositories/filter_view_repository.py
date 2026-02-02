"""FilterView repository for DynamoDB operations."""
from typing import Any

from app.core.config import settings
from app.models.filter_view import FilterView
from app.repositories.base import BaseRepository


class FilterViewRepository(BaseRepository[FilterView]):
    """Repository for FilterView entity operations.

    Provides CRUD operations and dashboard-based listing using GSI.
    """

    def __init__(self) -> None:
        """Initialize FilterViewRepository with filter_views table configuration."""
        super().__init__(
            table_name=f"{settings.dynamodb_table_prefix}filter_views",
            pk_name='filterViewId',
            model=FilterView
        )

    async def list_by_dashboard(self, dashboard_id: str, dynamodb: Any) -> list[FilterView]:
        """Retrieve all filter views for a specific dashboard.

        Uses the FilterViewsByDashboard GSI with dashboardId as HASH key
        and createdAt as RANGE key.

        Args:
            dashboard_id: Dashboard ID to filter by
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            List of FilterView instances for the given dashboard
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(
            table.query(
                IndexName='FilterViewsByDashboard',
                KeyConditionExpression='dashboardId = :dashboardId',
                ExpressionAttributeValues={':dashboardId': dashboard_id}
            )
        )

        items = response.get('Items', [])
        if not items:
            return []

        return [
            self.model(**self._from_dynamodb_item(item))
            for item in items
        ]
