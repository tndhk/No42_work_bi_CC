"""Transform repository for DynamoDB operations."""
from typing import Any

from app.core.config import settings
from app.models.transform import Transform
from app.repositories.base import BaseRepository


class TransformRepository(BaseRepository[Transform]):
    """Repository for Transform entity operations.

    Provides CRUD operations and owner-based listing using GSI.
    """

    def __init__(self) -> None:
        """Initialize TransformRepository with transforms table configuration."""
        super().__init__(
            table_name=f"{settings.dynamodb_table_prefix}transforms",
            pk_name='transformId',
            model=Transform
        )

    async def list_by_owner(self, owner_id: str, dynamodb: Any) -> list[Transform]:
        """Retrieve all transforms owned by a specific user.

        Args:
            owner_id: Owner user ID
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            List of Transform instances
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(
            table.query(
                IndexName='TransformsByOwner',
                KeyConditionExpression='ownerId = :ownerId',
                ExpressionAttributeValues={':ownerId': owner_id}
            )
        )

        items = response.get('Items', [])
        if not items:
            return []

        # Convert all items from DynamoDB format
        return [
            self.model(**self._from_dynamodb_item(item))
            for item in items
        ]
