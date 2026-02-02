"""Tests for GroupRepository."""
import pytest
from datetime import datetime
from typing import Any


@pytest.mark.asyncio
class TestGroupRepository:
    """Test suite for GroupRepository."""

    async def test_create_group(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating a group with automatic timestamp setting."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        group_data = {
            'id': 'group_abc123',
            'name': 'Engineering',
        }

        group = await repo.create(group_data, dynamodb)

        assert group.id == 'group_abc123'
        assert group.name == 'Engineering'
        assert isinstance(group.created_at, datetime)
        assert isinstance(group.updated_at, datetime)

    async def test_get_by_id_exists(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving group by ID when it exists."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        # Create first, then retrieve
        await repo.create(
            {'id': 'group_abc123', 'name': 'Engineering'},
            dynamodb,
        )

        group = await repo.get_by_id('group_abc123', dynamodb)

        assert group is not None
        assert group.id == 'group_abc123'
        assert group.name == 'Engineering'

    async def test_get_by_id_not_found(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving group by ID when it does not exist returns None."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        group = await repo.get_by_id('nonexistent', dynamodb)

        assert group is None

    async def test_get_by_name_exists(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving group by name using GroupsByName GSI."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        await repo.create(
            {'id': 'group_abc123', 'name': 'Engineering'},
            dynamodb,
        )

        group = await repo.get_by_name('Engineering', dynamodb)

        assert group is not None
        assert group.id == 'group_abc123'
        assert group.name == 'Engineering'

    async def test_get_by_name_not_found(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving group by name when it does not exist returns None."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        group = await repo.get_by_name('NonExistent', dynamodb)

        assert group is None

    async def test_update_group(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating a group name."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        await repo.create(
            {'id': 'group_abc123', 'name': 'Engineering'},
            dynamodb,
        )

        updated = await repo.update(
            'group_abc123',
            {'name': 'Platform Engineering'},
            dynamodb,
        )

        assert updated is not None
        assert updated.name == 'Platform Engineering'

    async def test_update_group_not_found(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating a non-existent group returns None."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        result = await repo.update('nonexistent', {'name': 'New Name'}, dynamodb)

        assert result is None

    async def test_delete_group(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a group."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        await repo.create(
            {'id': 'group_abc123', 'name': 'Engineering'},
            dynamodb,
        )

        await repo.delete('group_abc123', dynamodb)

        # Verify deletion
        group = await repo.get_by_id('group_abc123', dynamodb)
        assert group is None

    async def test_list_all(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing all groups."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        await repo.create({'id': 'group_1', 'name': 'Team A'}, dynamodb)
        await repo.create({'id': 'group_2', 'name': 'Team B'}, dynamodb)

        groups = await repo.list_all(dynamodb)

        assert len(groups) == 2
        names = {g.name for g in groups}
        assert 'Team A' in names
        assert 'Team B' in names

    async def test_list_all_empty(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing groups when table is empty returns empty list."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        groups = await repo.list_all(dynamodb)

        assert groups == []

    async def test_timestamps_on_create(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that created_at and updated_at are set on creation."""
        from app.repositories.group_repository import GroupRepository

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        group = await repo.create(
            {'id': 'group_ts', 'name': 'Timestamps Test'},
            dynamodb,
        )

        assert isinstance(group.created_at, datetime)
        assert isinstance(group.updated_at, datetime)
        assert group.created_at <= group.updated_at

    async def test_timestamps_on_update(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that updated_at changes on update while created_at remains."""
        from app.repositories.group_repository import GroupRepository
        import time

        tables, dynamodb = dynamodb_tables
        repo = GroupRepository()

        created = await repo.create(
            {'id': 'group_ts', 'name': 'Original'},
            dynamodb,
        )
        created_at_timestamp = int(created.created_at.timestamp())

        time.sleep(1.0)  # Ensure timestamp difference

        updated = await repo.update('group_ts', {'name': 'Updated'}, dynamodb)

        assert updated is not None
        assert int(updated.created_at.timestamp()) == created_at_timestamp
        assert updated.updated_at > created.updated_at
