"""Dataset repository for DynamoDB operations."""
from typing import Any

from app.core.config import settings
from app.models.dataset import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Repository for Dataset entity operations.

    Provides CRUD operations and owner-based listing using GSI.
    """

    def __init__(self) -> None:
        """Initialize DatasetRepository with datasets table configuration."""
        super().__init__(
            table_name=f"{settings.dynamodb_table_prefix}datasets",
            pk_name='datasetId',
            model=Dataset
        )

    async def list_by_owner(self, owner_id: str, dynamodb: Any) -> list[Dataset]:
        """Retrieve all datasets owned by a specific user.

        Args:
            owner_id: Owner user ID
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            List of Dataset instances
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(
            table.query(
                IndexName='DatasetsByOwner',
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
