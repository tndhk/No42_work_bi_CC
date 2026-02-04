"""Tests for DashboardRepository."""
import pytest
from datetime import datetime
from typing import Any



@pytest.mark.asyncio
class TestDashboardRepository:
    """Test suite for DashboardRepository."""

    async def test_create_dashboard(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating a dashboard with automatic timestamp setting."""
        from app.repositories.dashboard_repository import DashboardRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardRepository()

        dashboard_data = {
            'id': 'dashboard-001',
            'name': 'Test Dashboard',
            'description': 'A test dashboard',
            'layout': [
                {'card_id': 'card-001', 'x': 0, 'y': 0, 'w': 6, 'h': 4},
                {'card_id': 'card-002', 'x': 6, 'y': 0, 'w': 6, 'h': 4}
            ],
            'ownerId': 'owner-123'
        }

        dashboard = await repo.create(dashboard_data, dynamodb)

        assert dashboard.id == 'dashboard-001'
        assert dashboard.name == 'Test Dashboard'
        assert len(dashboard.layout) == 2
        assert dashboard.layout[0].card_id == 'card-001'
        assert isinstance(dashboard.created_at, datetime)
        assert isinstance(dashboard.updated_at, datetime)

    async def test_get_by_id_exists(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving dashboard by ID when it exists."""
        from app.repositories.dashboard_repository import DashboardRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['dashboards']
        now = datetime.now()
        table.put_item(
            Item={
                'dashboardId': 'dashboard-003',
                'name': 'Existing Dashboard',
                'description': 'Description',
                'layout': [
                    {'cardId': 'card-001', 'x': 0, 'y': 0, 'w': 12, 'h': 6}
                ],
                'ownerId': 'owner-123',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = DashboardRepository()
        dashboard = await repo.get_by_id('dashboard-003', dynamodb)

        assert dashboard is not None
        assert dashboard.id == 'dashboard-003'
        assert dashboard.name == 'Existing Dashboard'
        assert len(dashboard.layout) == 1

    async def test_get_by_id_not_found(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving dashboard by ID when it does not exist."""
        from app.repositories.dashboard_repository import DashboardRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardRepository()
        dashboard = await repo.get_by_id('dashboard-nonexistent', dynamodb)

        assert dashboard is None

    async def test_list_by_owner(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving dashboards by owner using GSI."""
        from app.repositories.dashboard_repository import DashboardRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['dashboards']
        now = datetime.now()

        # Create multiple dashboards for same owner
        for i in range(3):
            table.put_item(
                Item={
                    'dashboardId': f'dashboard-{i:03d}',
                    'name': f'Dashboard {i}',
                    'ownerId': 'owner-456',
                    'createdAt': int(now.timestamp()),
                    'updatedAt': int(now.timestamp())
                }
            )

        # Create dashboard for different owner
        table.put_item(
            Item={
                'dashboardId': 'dashboard-other',
                'name': 'Other Dashboard',
                'ownerId': 'owner-999',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = DashboardRepository()
        dashboards = await repo.list_by_owner('owner-456', dynamodb)

        assert len(dashboards) == 3
        assert all(d.id.startswith('dashboard-') for d in dashboards)
        # Should not include other owner's dashboards
        assert not any(d.id == 'dashboard-other' for d in dashboards)

    async def test_update_dashboard(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating dashboard layout and metadata."""
        from app.repositories.dashboard_repository import DashboardRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['dashboards']
        original_time = datetime(2024, 1, 1)
        table.put_item(
            Item={
                'dashboardId': 'dashboard-update',
                'name': 'Old Name',
                'layout': [
                    {'cardId': 'card-old', 'x': 0, 'y': 0, 'w': 6, 'h': 4}
                ],
                'ownerId': 'owner-123',
                'createdAt': int(original_time.timestamp()),
                'updatedAt': int(original_time.timestamp())
            }
        )

        repo = DashboardRepository()
        update_data = {
            'name': 'New Name',
            'layout': [
                {'card_id': 'card-new-1', 'x': 0, 'y': 0, 'w': 6, 'h': 4},
                {'card_id': 'card-new-2', 'x': 6, 'y': 0, 'w': 6, 'h': 4}
            ]
        }
        updated = await repo.update('dashboard-update', update_data, dynamodb)

        assert updated is not None
        assert updated.name == 'New Name'
        assert len(updated.layout) == 2
        assert updated.layout[0].card_id == 'card-new-1'
        assert updated.updated_at.timestamp() > original_time.timestamp()

    async def test_delete_dashboard(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a dashboard."""
        from app.repositories.dashboard_repository import DashboardRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['dashboards']
        now = datetime.now()
        table.put_item(
            Item={
                'dashboardId': 'dashboard-delete',
                'name': 'To Delete',
                'ownerId': 'owner-123',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = DashboardRepository()
        await repo.delete('dashboard-delete', dynamodb)

        # Verify deletion
        response = table.get_item(Key={'dashboardId': 'dashboard-delete'})
        assert 'Item' not in response

    async def test_timestamps(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that created_at and updated_at are properly managed."""
        from app.repositories.dashboard_repository import DashboardRepository

        tables, dynamodb = dynamodb_tables
        repo = DashboardRepository()

        dashboard_data = {
            'id': 'dashboard-timestamps',
            'name': 'Test Dashboard',
            'ownerId': 'owner-123'
        }

        created = await repo.create(dashboard_data, dynamodb)
        assert isinstance(created.created_at, datetime)
        assert isinstance(created.updated_at, datetime)
        assert created.created_at <= created.updated_at

        # Store original created_at timestamp (in seconds since DynamoDB stores as integer)
        created_at_timestamp = int(created.created_at.timestamp())

        # Update and verify updated_at changes
        import time
        time.sleep(1.0)  # Sleep 1 second to ensure timestamp changes
        updated = await repo.update('dashboard-timestamps', {'name': 'Updated Name'}, dynamodb)
        assert int(updated.created_at.timestamp()) == created_at_timestamp
        assert updated.updated_at > created.updated_at
