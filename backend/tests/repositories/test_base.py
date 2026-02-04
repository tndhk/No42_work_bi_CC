"""Tests for BaseRepository."""
import pytest
from datetime import datetime
from typing import Any
from pydantic import BaseModel

from app.core.config import settings


class TestModel(BaseModel):
    """Test model for BaseRepository testing."""

    id: str
    name: str
    created_at: datetime
    updated_at: datetime


@pytest.mark.asyncio
class TestBaseRepository:
    """Test suite for BaseRepository."""

    async def test_create_item(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating an item with automatic timestamp setting."""
        from app.repositories.base import BaseRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        _ = tables['users']
        repo = BaseRepository[TestModel](
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=TestModel
        )

        # Create test data
        test_data = {
            'id': 'test-id-123',
            'name': 'Test User'
        }

        # Execute
        created = await repo.create(test_data, dynamodb)

        # Verify
        assert created.id == 'test-id-123'
        assert created.name == 'Test User'
        assert isinstance(created.created_at, datetime)
        assert isinstance(created.updated_at, datetime)
        assert created.created_at == created.updated_at

    async def test_get_by_id_existing(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving an existing item by ID."""
        from app.repositories.base import BaseRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        now_timestamp = datetime.now().timestamp()
        table.put_item(
            Item={
                'userId': 'user-123',
                'name': 'John Doe',
                'createdAt': int(now_timestamp),
                'updatedAt': int(now_timestamp)
            }
        )

        repo = BaseRepository[TestModel](
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=TestModel
        )

        # Execute
        result = await repo.get_by_id('user-123', dynamodb)

        # Verify
        assert result is not None
        assert result.id == 'user-123'
        assert result.name == 'John Doe'

    async def test_get_by_id_nonexistent(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving a non-existent item returns None."""
        from app.repositories.base import BaseRepository

        # Setup
        tables, dynamodb = dynamodb_tables

        repo = BaseRepository[TestModel](
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=TestModel
        )

        # Execute
        result = await repo.get_by_id('nonexistent-id', dynamodb)

        # Verify
        assert result is None

    async def test_update_item(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating an item with automatic updatedAt timestamp."""
        from app.repositories.base import BaseRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        original_timestamp = datetime(2024, 1, 1).timestamp()
        table.put_item(
            Item={
                'userId': 'user-456',
                'name': 'Original Name',
                'createdAt': int(original_timestamp),
                'updatedAt': int(original_timestamp)
            }
        )

        repo = BaseRepository[TestModel](
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=TestModel
        )

        # Execute
        update_data = {'name': 'Updated Name'}
        updated = await repo.update('user-456', update_data, dynamodb)

        # Verify
        assert updated is not None
        assert updated.id == 'user-456'
        assert updated.name == 'Updated Name'
        assert updated.created_at.timestamp() == pytest.approx(original_timestamp, rel=1)
        assert updated.updated_at.timestamp() > original_timestamp

    async def test_update_nonexistent_item(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating a non-existent item returns None."""
        from app.repositories.base import BaseRepository

        # Setup
        tables, dynamodb = dynamodb_tables

        repo = BaseRepository[TestModel](
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=TestModel
        )

        # Execute
        result = await repo.update('nonexistent-id', {'name': 'Test'}, dynamodb)

        # Verify
        assert result is None

    async def test_delete_item(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting an existing item."""
        from app.repositories.base import BaseRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        now_timestamp = datetime.now().timestamp()
        table.put_item(
            Item={
                'userId': 'user-789',
                'name': 'To Delete',
                'createdAt': int(now_timestamp),
                'updatedAt': int(now_timestamp)
            }
        )

        repo = BaseRepository[TestModel](
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=TestModel
        )

        # Execute
        await repo.delete('user-789', dynamodb)

        # Verify - item should be gone
        response = table.get_item(Key={'userId': 'user-789'})
        assert 'Item' not in response

    async def test_immutability_on_create(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that create returns a new object (immutability)."""
        from app.repositories.base import BaseRepository

        # Setup
        tables, dynamodb = dynamodb_tables

        repo = BaseRepository[TestModel](
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=TestModel
        )

        # Create test data
        original_data = {
            'id': 'immutable-test',
            'name': 'Original'
        }

        # Execute
        result = await repo.create(original_data, dynamodb)

        # Verify - result should be a new object
        assert result.model_dump() != original_data  # Different due to timestamps
        assert original_data.get('created_at') is None  # Original unchanged
        assert original_data.get('updated_at') is None  # Original unchanged

    async def test_immutability_on_update(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that update returns a new object (immutability)."""
        from app.repositories.base import BaseRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['users']
        now_timestamp = datetime.now().timestamp()
        table.put_item(
            Item={
                'userId': 'immutable-update',
                'name': 'Before Update',
                'createdAt': int(now_timestamp),
                'updatedAt': int(now_timestamp)
            }
        )

        repo = BaseRepository[TestModel](
            table_name=f"{settings.dynamodb_table_prefix}users",
            pk_name='userId',
            model=TestModel
        )

        # Execute
        update_data = {'name': 'After Update'}
        result = await repo.update('immutable-update', update_data, dynamodb)

        # Verify
        assert result is not None
        assert result.name == 'After Update'
        # Original update_data should be unchanged
        assert update_data == {'name': 'After Update'}
