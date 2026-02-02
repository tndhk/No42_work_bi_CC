"""Group repository for DynamoDB operations."""
from typing import Any, Optional

from app.core.config import settings
from app.models.group import Group
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group]):
    """Repository for Group entity operations.

    Provides CRUD operations and name-based lookup using GSI.
    """

    def __init__(self) -> None:
        """Initialize GroupRepository with groups table configuration."""
        super().__init__(
            table_name=f"{settings.dynamodb_table_prefix}groups",
            pk_name='groupId',
            model=Group
        )

    async def get_by_name(self, name: str, dynamodb: Any) -> Optional[Group]:
        """Retrieve group by name using GroupsByName GSI.

        Args:
            name: Group name to search for
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            Group instance if found, None otherwise
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(
            table.query(
                IndexName='GroupsByName',
                KeyConditionExpression='#n = :name',
                ExpressionAttributeNames={'#n': 'name'},
                ExpressionAttributeValues={':name': name}
            )
        )

        items = response.get('Items', [])
        if not items:
            return None

        python_dict = self._from_dynamodb_item(items[0])
        return self.model(**python_dict)

    async def list_all(self, dynamodb: Any) -> list[Group]:
        """List all groups.

        Args:
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            List of all Group instances
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(table.scan())

        items = response.get('Items', [])
        if not items:
            return []

        return [
            self.model(**self._from_dynamodb_item(item))
            for item in items
        ]
