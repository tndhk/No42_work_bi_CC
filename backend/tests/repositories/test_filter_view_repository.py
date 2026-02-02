"""Tests for FilterViewRepository."""
import pytest
from datetime import datetime
from typing import Any


@pytest.mark.asyncio
class TestFilterViewRepository:
    """Test suite for FilterViewRepository CRUD operations."""

    async def test_create_and_get(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating and retrieving a filter view."""
        from app.repositories.filter_view_repository import FilterViewRepository

        tables, dynamodb = dynamodb_tables
        repo = FilterViewRepository()

        data = {
            'id': 'fv_test001',
            'dashboard_id': 'dashboard_abc',
            'name': 'My View',
            'owner_id': 'user_123',
            'filter_state': {'category': 'sales'},
            'is_shared': False,
            'is_default': False,
        }
        created = await repo.create(data, dynamodb)
        assert created.id == 'fv_test001'
        assert created.name == 'My View'
        assert created.dashboard_id == 'dashboard_abc'
        assert created.owner_id == 'user_123'
        assert created.filter_state == {'category': 'sales'}
        assert created.is_shared is False
        assert created.is_default is False
        assert isinstance(created.created_at, datetime)
        assert isinstance(created.updated_at, datetime)

        retrieved = await repo.get_by_id('fv_test001', dynamodb)
        assert retrieved is not None
        assert retrieved.id == 'fv_test001'
        assert retrieved.name == 'My View'
        assert retrieved.dashboard_id == 'dashboard_abc'

    async def test_get_nonexistent(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving non-existent filter view returns None."""
        from app.repositories.filter_view_repository import FilterViewRepository

        tables, dynamodb = dynamodb_tables
        repo = FilterViewRepository()

        result = await repo.get_by_id('fv_nonexistent', dynamodb)
        assert result is None

    async def test_list_by_dashboard(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing filter views by dashboard ID using GSI."""
        from app.repositories.filter_view_repository import FilterViewRepository

        tables, dynamodb = dynamodb_tables
        repo = FilterViewRepository()

        # Create two views for the same dashboard
        for i in range(2):
            await repo.create({
                'id': f'fv_dash1_{i}',
                'dashboard_id': 'dashboard_abc',
                'name': f'View {i}',
                'owner_id': 'user_123',
                'filter_state': {'key': f'val{i}'},
                'is_shared': False,
                'is_default': False,
            }, dynamodb)

        # Create one view for a different dashboard
        await repo.create({
            'id': 'fv_other',
            'dashboard_id': 'dashboard_xyz',
            'name': 'Other View',
            'owner_id': 'user_123',
            'filter_state': {},
            'is_shared': False,
            'is_default': False,
        }, dynamodb)

        results = await repo.list_by_dashboard('dashboard_abc', dynamodb)
        assert len(results) == 2
        assert all(r.dashboard_id == 'dashboard_abc' for r in results)
        # Should not include other dashboard's views
        assert not any(r.id == 'fv_other' for r in results)

    async def test_list_by_dashboard_empty(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing filter views for a dashboard with no views returns empty list."""
        from app.repositories.filter_view_repository import FilterViewRepository

        tables, dynamodb = dynamodb_tables
        repo = FilterViewRepository()

        results = await repo.list_by_dashboard('dashboard_empty', dynamodb)
        assert results == []

    async def test_update(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating a filter view."""
        from app.repositories.filter_view_repository import FilterViewRepository

        tables, dynamodb = dynamodb_tables
        repo = FilterViewRepository()

        await repo.create({
            'id': 'fv_update',
            'dashboard_id': 'dashboard_abc',
            'name': 'Original',
            'owner_id': 'user_123',
            'filter_state': {'a': 1},
            'is_shared': False,
            'is_default': False,
        }, dynamodb)

        updated = await repo.update('fv_update', {'name': 'Updated'}, dynamodb)
        assert updated is not None
        assert updated.name == 'Updated'
        # Verify other fields are preserved
        assert updated.dashboard_id == 'dashboard_abc'
        assert updated.filter_state == {'a': 1}

    async def test_update_nonexistent(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating a non-existent filter view returns None."""
        from app.repositories.filter_view_repository import FilterViewRepository

        tables, dynamodb = dynamodb_tables
        repo = FilterViewRepository()

        result = await repo.update('fv_nonexistent', {'name': 'New'}, dynamodb)
        assert result is None

    async def test_delete(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a filter view."""
        from app.repositories.filter_view_repository import FilterViewRepository

        tables, dynamodb = dynamodb_tables
        repo = FilterViewRepository()

        await repo.create({
            'id': 'fv_delete',
            'dashboard_id': 'dashboard_abc',
            'name': 'To Delete',
            'owner_id': 'user_123',
            'filter_state': {},
            'is_shared': False,
            'is_default': False,
        }, dynamodb)

        await repo.delete('fv_delete', dynamodb)
        result = await repo.get_by_id('fv_delete', dynamodb)
        assert result is None

    async def test_timestamps_on_create(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that created_at and updated_at are set on create."""
        from app.repositories.filter_view_repository import FilterViewRepository

        tables, dynamodb = dynamodb_tables
        repo = FilterViewRepository()

        created = await repo.create({
            'id': 'fv_timestamps',
            'dashboard_id': 'dashboard_abc',
            'name': 'Timestamps Test',
            'owner_id': 'user_123',
            'filter_state': {},
            'is_shared': False,
            'is_default': False,
        }, dynamodb)

        assert isinstance(created.created_at, datetime)
        assert isinstance(created.updated_at, datetime)
        assert created.created_at <= created.updated_at
