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
