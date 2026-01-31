#!/bin/bash

# Since the files are corrupted, we'll recreate the dataset repository test file

cat > tests/repositories/test_dataset_repository_new.py <<'PYTHON'
"""Tests for DatasetRepository."""
import pytest
from datetime import datetime
from typing import Any

from app.core.config import settings


@pytest.mark.asyncio
class TestDatasetRepository:
    """Test suite for DatasetRepository."""

    async def test_create_dataset(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating a dataset with automatic timestamp setting."""
        from app.repositories.dataset_repository import DatasetRepository

        tables, dynamodb = dynamodb_tables
        repo = DatasetRepository()

        dataset_data = {
            'id': 'dataset-001',
            'name': 'Test Dataset',
            'description': 'A test dataset',
            'source_type': 'csv',
            'row_count': 100,
            'columns': [
                {'name': 'id', 'data_type': 'int64', 'nullable': False},
                {'name': 'name', 'data_type': 'string', 'nullable': True}
            ],
            'ownerId': 'owner-123'
        }

        dataset = await repo.create(dataset_data, dynamodb)

        assert dataset.id == 'dataset-001'
        assert dataset.name == 'Test Dataset'
        assert dataset.source_type == 'csv'
        assert dataset.row_count == 100
        assert len(dataset.columns) == 2
        assert isinstance(dataset.created_at, datetime)
        assert isinstance(dataset.updated_at, datetime)

    async def test_get_by_id(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving dataset by ID."""
        from app.repositories.dataset_repository import DatasetRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['datasets']
        now = datetime.now()
        table.put_item(
            Item={
                'datasetId': 'dataset-002',
                'name': 'Existing Dataset',
                'description': 'Description',
                'sourceType': 'csv',
                'rowCount': 50,
                'schema': [
                    {'name': 'col1', 'dataType': 'int64', 'nullable': False}
                ],
                'ownerId': 'owner-123',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = DatasetRepository()
        dataset = await repo.get_by_id('dataset-002', dynamodb)

        assert dataset is not None
        assert dataset.id == 'dataset-002'
        assert dataset.name == 'Existing Dataset'
        assert dataset.row_count == 50

    async def test_list_by_owner(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving datasets by owner using GSI."""
        from app.repositories.dataset_repository import DatasetRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['datasets']
        now = datetime.now()

        # Create multiple datasets for same owner
        for i in range(3):
            table.put_item(
                Item={
                    'datasetId': f'dataset-{i:03d}',
                    'name': f'Dataset {i}',
                    'sourceType': 'csv',
                    'rowCount': i * 10,
                    'schema': [],
                    'ownerId': 'owner-456',
                    'createdAt': int(now.timestamp()),
                    'updatedAt': int(now.timestamp())
                }
            )

        # Create dataset for different owner
        table.put_item(
            Item={
                'datasetId': 'dataset-other',
                'name': 'Other Dataset',
                'sourceType': 'csv',
                'rowCount': 10,
                'schema': [],
                'ownerId': 'owner-999',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = DatasetRepository()
        datasets = await repo.list_by_owner('owner-456', dynamodb)

        assert len(datasets) == 3
        assert all(d.id.startswith('dataset-') for d in datasets)
        # Should not include other owner's datasets
        assert not any(d.id == 'dataset-other' for d in datasets)

    async def test_list_by_owner_empty(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test listing datasets for owner with no datasets."""
        from app.repositories.dataset_repository import DatasetRepository

        tables, dynamodb = dynamodb_tables
        repo = DatasetRepository()
        datasets = await repo.list_by_owner('owner-nonexistent', dynamodb)

        assert datasets == []

    async def test_update_dataset(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating dataset metadata."""
        from app.repositories.dataset_repository import DatasetRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['datasets']
        original_time = datetime(2024, 1, 1)
        table.put_item(
            Item={
                'datasetId': 'dataset-update',
                'name': 'Old Name',
                'description': 'Old Description',
                'sourceType': 'csv',
                'rowCount': 100,
                'schema': [],
                'ownerId': 'owner-123',
                'createdAt': int(original_time.timestamp()),
                'updatedAt': int(original_time.timestamp())
            }
        )

        repo = DatasetRepository()
        update_data = {
            'name': 'New Name',
            'description': 'New Description'
        }
        updated = await repo.update('dataset-update', update_data, dynamodb)

        assert updated is not None
        assert updated.name == 'New Name'
        assert updated.description == 'New Description'
        assert updated.source_type == 'csv'  # Unchanged
        assert updated.updated_at.timestamp() > original_time.timestamp()

    async def test_delete_dataset(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a dataset."""
        from app.repositories.dataset_repository import DatasetRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['datasets']
        now = datetime.now()
        table.put_item(
            Item={
                'datasetId': 'dataset-delete',
                'name': 'To Delete',
                'sourceType': 'csv',
                'rowCount': 10,
                'schema': [],
                'ownerId': 'owner-123',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = DatasetRepository()
        await repo.delete('dataset-delete', dynamodb)

        # Verify deletion
        response = table.get_item(Key={'datasetId': 'dataset-delete'})
        assert 'Item' not in response

    async def test_immutability(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that repository operations return new objects."""
        from app.repositories.dataset_repository import DatasetRepository

        tables, dynamodb = dynamodb_tables
        repo = DatasetRepository()

        dataset_data = {
            'id': 'dataset-immutable',
            'name': 'Test',
            'source_type': 'csv',
            'row_count': 10,
            'columns': [],
            'ownerId': 'owner-123'
        }

        original_data = dataset_data.copy()
        result = await repo.create(dataset_data, dynamodb)

        # Original data unchanged (except timestamps were added to result)
        assert dataset_data == original_data
        assert result.name == 'Test'
        assert isinstance(result.created_at, datetime)
PYTHON

mv tests/repositories/test_dataset_repository_new.py tests/repositories/test_dataset_repository.py
echo "Created test_dataset_repository.py"
