"""Tests for TransformRepository."""
import pytest
from datetime import datetime
from typing import Any

from app.core.config import settings


@pytest.mark.asyncio
class TestTransformRepository:
    """Test suite for TransformRepository."""

    async def test_create_transform(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test creating a transform with automatic timestamp setting."""
        from app.repositories.transform_repository import TransformRepository

        tables, dynamodb = dynamodb_tables_with_transforms
        repo = TransformRepository()

        transform_data = {
            'id': 'transform-001',
            'name': 'Test Transform',
            'code': 'df.filter(col("value") > 10)',
            'input_dataset_ids': ['dataset-001', 'dataset-002'],
            'output_dataset_id': 'dataset-out-001',
            'owner_id': 'owner-123'
        }

        transform = await repo.create(transform_data, dynamodb)

        assert transform.id == 'transform-001'
        assert transform.name == 'Test Transform'
        assert transform.code == 'df.filter(col("value") > 10)'
        assert transform.input_dataset_ids == ['dataset-001', 'dataset-002']
        assert transform.output_dataset_id == 'dataset-out-001'
        assert transform.owner_id == 'owner-123'
        assert isinstance(transform.created_at, datetime)
        assert isinstance(transform.updated_at, datetime)

    async def test_get_by_id_exists(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving transform by ID when it exists."""
        from app.repositories.transform_repository import TransformRepository

        # Setup
        tables, dynamodb = dynamodb_tables_with_transforms
        table = tables['transforms']
        now = datetime.now()
        table.put_item(
            Item={
                'transformId': 'transform-003',
                'name': 'Existing Transform',
                'code': 'df.select("col1", "col2")',
                'inputDatasetIds': ['dataset-001'],
                'outputDatasetId': None,
                'ownerId': 'owner-123',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = TransformRepository()
        transform = await repo.get_by_id('transform-003', dynamodb)

        assert transform is not None
        assert transform.id == 'transform-003'
        assert transform.name == 'Existing Transform'
        assert 'select' in transform.code

    async def test_get_by_id_not_found(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving transform by ID when it does not exist."""
        from app.repositories.transform_repository import TransformRepository

        tables, dynamodb = dynamodb_tables_with_transforms
        repo = TransformRepository()
        transform = await repo.get_by_id('transform-nonexistent', dynamodb)

        assert transform is None

    async def test_list_by_owner(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving transforms by owner using GSI."""
        from app.repositories.transform_repository import TransformRepository

        # Setup
        tables, dynamodb = dynamodb_tables_with_transforms
        table = tables['transforms']
        now = datetime.now()

        # Create multiple transforms for same owner
        for i in range(3):
            table.put_item(
                Item={
                    'transformId': f'transform-{i:03d}',
                    'name': f'Transform {i}',
                    'code': f'df.filter({i})',
                    'inputDatasetIds': ['dataset-001'],
                    'ownerId': 'owner-456',
                    'createdAt': int(now.timestamp()) + i,  # Different timestamps for ordering
                    'updatedAt': int(now.timestamp()) + i
                }
            )

        # Create transform for different owner
        table.put_item(
            Item={
                'transformId': 'transform-other',
                'name': 'Other Transform',
                'code': 'df.other()',
                'inputDatasetIds': ['dataset-002'],
                'ownerId': 'owner-999',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = TransformRepository()
        transforms = await repo.list_by_owner('owner-456', dynamodb)

        assert len(transforms) == 3
        assert all(t.id.startswith('transform-') for t in transforms)
        # Should not include other owner's transforms
        assert not any(t.id == 'transform-other' for t in transforms)

    async def test_list_by_owner_empty(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving transforms for owner with no transforms."""
        from app.repositories.transform_repository import TransformRepository

        tables, dynamodb = dynamodb_tables_with_transforms
        repo = TransformRepository()
        transforms = await repo.list_by_owner('owner-nonexistent', dynamodb)

        assert transforms == []

    async def test_update_transform(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test updating transform code and metadata."""
        from app.repositories.transform_repository import TransformRepository

        # Setup
        tables, dynamodb = dynamodb_tables_with_transforms
        table = tables['transforms']
        original_time = datetime(2024, 1, 1)
        table.put_item(
            Item={
                'transformId': 'transform-update',
                'name': 'Old Name',
                'code': 'old_code',
                'inputDatasetIds': ['dataset-001'],
                'ownerId': 'owner-123',
                'createdAt': int(original_time.timestamp()),
                'updatedAt': int(original_time.timestamp())
            }
        )

        repo = TransformRepository()
        update_data = {
            'name': 'New Name',
            'code': 'new_code',
            'input_dataset_ids': ['dataset-new']
        }
        updated = await repo.update('transform-update', update_data, dynamodb)

        assert updated is not None
        assert updated.name == 'New Name'
        assert updated.code == 'new_code'
        assert updated.input_dataset_ids == ['dataset-new']
        assert updated.updated_at.timestamp() > original_time.timestamp()

    async def test_update_nonexistent_transform(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test updating a transform that does not exist."""
        from app.repositories.transform_repository import TransformRepository

        tables, dynamodb = dynamodb_tables_with_transforms
        repo = TransformRepository()
        update_data = {'name': 'New Name'}
        updated = await repo.update('transform-nonexistent', update_data, dynamodb)

        assert updated is None

    async def test_delete_transform(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a transform."""
        from app.repositories.transform_repository import TransformRepository

        # Setup
        tables, dynamodb = dynamodb_tables_with_transforms
        table = tables['transforms']
        now = datetime.now()
        table.put_item(
            Item={
                'transformId': 'transform-delete',
                'name': 'To Delete',
                'code': 'df.delete()',
                'inputDatasetIds': ['dataset-001'],
                'ownerId': 'owner-123',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = TransformRepository()
        await repo.delete('transform-delete', dynamodb)

        # Verify deletion
        response = table.get_item(Key={'transformId': 'transform-delete'})
        assert 'Item' not in response

    async def test_timestamps(self, dynamodb_tables_with_transforms: tuple[dict[str, Any], Any]) -> None:
        """Test that created_at and updated_at are properly managed."""
        from app.repositories.transform_repository import TransformRepository

        tables, dynamodb = dynamodb_tables_with_transforms
        repo = TransformRepository()

        transform_data = {
            'id': 'transform-timestamps',
            'name': 'Test Transform',
            'code': 'test_code',
            'input_dataset_ids': ['dataset-001'],
            'owner_id': 'owner-123'
        }

        created = await repo.create(transform_data, dynamodb)
        assert isinstance(created.created_at, datetime)
        assert isinstance(created.updated_at, datetime)
        assert created.created_at <= created.updated_at

        # Store original created_at timestamp (in seconds since DynamoDB stores as integer)
        created_at_timestamp = int(created.created_at.timestamp())

        # Update and verify updated_at changes
        import time
        time.sleep(1.0)  # Sleep 1 second to ensure timestamp changes
        updated = await repo.update('transform-timestamps', {'name': 'Updated Name'}, dynamodb)
        assert int(updated.created_at.timestamp()) == created_at_timestamp
        assert updated.updated_at > created.updated_at
