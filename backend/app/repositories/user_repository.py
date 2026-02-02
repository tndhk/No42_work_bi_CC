"""User repository for DynamoDB operations."""
from typing import Any, Optional

from app.core.config import settings
from app.models.user import UserInDB
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserInDB]):
    """Repository for User entity operations.

    Provides CRUD operations and email-based lookup using GSI.
    """

    def __init__(self) -> None:
        """Initialize UserRepository with users table configuration."""
        super().__init__(
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=UserInDB
        )

    def _from_dynamodb_item(self, item: dict) -> dict:
        """Convert DynamoDB item to Python dict with role default handling.

        Ensures backward compatibility for existing users without a role field.

        Args:
            item: DynamoDB item with camelCase keys

        Returns:
            Python dictionary with snake_case keys including role default
        """
        python_dict = super()._from_dynamodb_item(item)
        if 'role' not in python_dict:
            python_dict['role'] = 'user'
        return python_dict

    async def get_by_email(self, email: str, dynamodb: Any) -> Optional[UserInDB]:
        """Retrieve user by email using UsersByEmail GSI.

        Args:
            email: User email address
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            User instance if found, None otherwise
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(
            table.query(
                IndexName='UsersByEmail',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
        )

        items = response.get('Items', [])
        if not items:
            return None

        # Convert first match from DynamoDB format
        python_dict = self._from_dynamodb_item(items[0])
        return self.model(**python_dict)

    async def scan_by_email_prefix(self, query: str, limit: int, dynamodb: Any) -> list[UserInDB]:
        """Search users by email prefix using DynamoDB Scan.

        Args:
            query: Email search query (partial match)
            limit: Maximum number of results
            dynamodb: DynamoDB resource

        Returns:
            List of matching users
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)

        response = await self._execute_db_operation(
            table.scan(
                FilterExpression='contains(email, :query)',
                ExpressionAttributeValues={':query': query},
                Limit=limit * 3,  # Scan more to account for filtering
            )
        )

        items = response.get('Items', [])
        results = []
        for item in items[:limit]:
            python_dict = self._from_dynamodb_item(item)
            results.append(self.model(**python_dict))

        return results
