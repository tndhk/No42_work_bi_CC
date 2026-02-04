"""Tests for UserRepository."""
import pytest
from datetime import datetime
from typing import Any



@pytest.mark.asyncio
class TestUserRepository:
    """Test suite for UserRepository."""

    async def test_create_user(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating a user with automatic timestamp setting."""
        from app.repositories.user_repository import UserRepository

        tables, dynamodb = dynamodb_tables
        repo = UserRepository()

        user_data = {
            'id': 'user-001',
            'email': 'test@example.com',
            'hashed_password': 'hashed_password_123'
        }

        user = await repo.create(user_data, dynamodb)

        assert user.id == 'user-001'
        assert user.email == 'test@example.com'
        assert user.hashed_password == 'hashed_password_123'
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    async def test_get_by_id(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving user by ID."""
        from app.repositories.user_repository import UserRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        now = datetime.now()
        table.put_item(
            Item={
                'userId': 'user-002',
                'email': 'get@example.com',
                'hashedPassword': 'hashed_pwd',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = UserRepository()
        user = await repo.get_by_id('user-002', dynamodb)

        assert user is not None
        assert user.id == 'user-002'
        assert user.email == 'get@example.com'

    async def test_get_by_email_existing(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving user by email using GSI."""
        from app.repositories.user_repository import UserRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        now = datetime.now()
        table.put_item(
            Item={
                'userId': 'user-003',
                'email': 'gsi@example.com',
                'hashedPassword': 'hashed_pwd',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = UserRepository()
        user = await repo.get_by_email('gsi@example.com', dynamodb)

        assert user is not None
        assert user.email == 'gsi@example.com'
        assert user.id == 'user-003'

    async def test_get_by_email_nonexistent(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving non-existent user by email returns None."""
        from app.repositories.user_repository import UserRepository

        tables, dynamodb = dynamodb_tables
        repo = UserRepository()
        user = await repo.get_by_email('nonexistent@example.com', dynamodb)

        assert user is None

    async def test_update_user(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating user with new hashed password."""
        from app.repositories.user_repository import UserRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        original_time = datetime(2024, 1, 1)
        table.put_item(
            Item={
                'userId': 'user-004',
                'email': 'update@example.com',
                'hashedPassword': 'old_hash',
                'createdAt': int(original_time.timestamp()),
                'updatedAt': int(original_time.timestamp())
            }
        )

        repo = UserRepository()
        update_data = {'hashed_password': 'new_hash'}
        updated = await repo.update('user-004', update_data, dynamodb)

        assert updated is not None
        assert updated.hashed_password == 'new_hash'
        assert updated.email == 'update@example.com'
        assert updated.updated_at.timestamp() > original_time.timestamp()

    async def test_delete_user(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a user."""
        from app.repositories.user_repository import UserRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        now = datetime.now()
        table.put_item(
            Item={
                'userId': 'user-005',
                'email': 'delete@example.com',
                'hashedPassword': 'hash',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = UserRepository()
        await repo.delete('user-005', dynamodb)

        # Verify deletion
        response = table.get_item(Key={'userId': 'user-005'})
        assert 'Item' not in response

    async def test_immutability(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that repository operations return new objects."""
        from app.repositories.user_repository import UserRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        now = datetime.now()
        table.put_item(
            Item={
                'userId': 'user-006',
                'email': 'immutable@example.com',
                'hashedPassword': 'old_hash',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = UserRepository()
        update_data = {'hashed_password': 'new_hash'}
        original_update_data = update_data.copy()
        result = await repo.update('user-006', update_data, dynamodb)

        # Original data unchanged
        assert update_data == original_update_data
        # Result is a new object with updated fields
        assert result is not None
        assert result.hashed_password == 'new_hash'
