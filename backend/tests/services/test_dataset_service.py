"""Tests for dataset_service module."""
import io
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.models.dataset import ColumnSchema, Dataset
from app.services.dataset_service import DatasetService


@pytest.fixture
def sample_csv_bytes() -> bytes:
    """Create sample CSV data as bytes."""
    csv_content = """name,age,email,active
Alice,25,alice@example.com,true
Bob,30,bob@example.com,false
Charlie,35,charlie@example.com,true
"""
    return csv_content.encode('utf-8')


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create sample DataFrame."""
    return pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com'],
        'active': [True, False, True]
    })


@pytest.fixture
def sample_schema() -> list[ColumnSchema]:
    """Create sample schema."""
    return [
        ColumnSchema(name='name', data_type='string', nullable=False),
        ColumnSchema(name='age', data_type='int64', nullable=False),
        ColumnSchema(name='email', data_type='string', nullable=False),
        ColumnSchema(name='active', data_type='bool', nullable=False),
    ]


@pytest.fixture
def mock_dynamodb() -> Any:
    """Create mock DynamoDB resource."""
    return MagicMock()


@pytest.fixture
def mock_s3_client() -> Any:
    """Create mock S3 client."""
    return MagicMock()


class TestDatasetServiceImportCSV:
    """Tests for import_csv method."""

    @pytest.mark.asyncio
    async def test_import_csv_full_pipeline_non_partitioned(
        self,
        sample_csv_bytes: bytes,
        mock_dynamodb: Any,
        mock_s3_client: Any,
    ) -> None:
        """Test full CSV import pipeline without partitioning.

        Verifies:
        - CSV parsing
        - Type inference
        - Parquet conversion and S3 upload
        - DynamoDB metadata storage
        - dataset_id format (ds_[12 hex chars])
        - Timestamp setting (last_import_at, last_import_by)
        - Schema storage
        - Row and column counts
        """
        # Arrange
        service = DatasetService()
        name = "Test Dataset"
        owner_id = "user_123"

        # Act
        result = await service.import_csv(
            file_bytes=sample_csv_bytes,
            name=name,
            owner_id=owner_id,
            dynamodb=mock_dynamodb,
            s3_client=mock_s3_client,
        )

        # Assert - dataset_id format
        assert result.id.startswith('ds_')
        assert len(result.id) == 15  # ds_ + 12 hex chars
        # Verify hex format
        hex_part = result.id[3:]
        assert all(c in '0123456789abcdef' for c in hex_part)

        # Assert - basic metadata
        assert result.name == name
        assert result.owner_id == owner_id
        assert result.source_type == 'csv'

        # Assert - counts
        assert result.row_count == 3
        assert result.column_count == 4

        # Assert - schema
        assert len(result.columns) == 4
        assert result.columns[0].name == 'name'
        assert result.columns[1].name == 'age'
        assert result.columns[2].name == 'email'
        assert result.columns[3].name == 'active'

        # Assert - timestamps
        assert result.last_import_at is not None
        assert isinstance(result.last_import_at, datetime)
        assert result.last_import_by == owner_id

        # Assert - S3 path
        assert result.s3_path is not None
        assert result.s3_path.startswith(f'datasets/{result.id}/')

        # Assert - S3 upload was called
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_csv_with_custom_encoding(
        self,
        mock_dynamodb: Any,
        mock_s3_client: Any,
    ) -> None:
        """Test CSV import with custom encoding (cp932)."""
        # Arrange
        service = DatasetService()
        csv_content = "名前,年齢\n太郎,25\n花子,30\n"
        csv_bytes = csv_content.encode('cp932')

        # Act
        result = await service.import_csv(
            file_bytes=csv_bytes,
            name="Japanese Data",
            owner_id="user_123",
            dynamodb=mock_dynamodb,
            s3_client=mock_s3_client,
            encoding='cp932',
        )

        # Assert
        assert result.row_count == 2
        assert result.columns[0].name == '名前'
        assert result.columns[1].name == '年齢'

    @pytest.mark.asyncio
    async def test_import_csv_with_custom_delimiter(
        self,
        mock_dynamodb: Any,
        mock_s3_client: Any,
    ) -> None:
        """Test CSV import with custom delimiter (tab)."""
        # Arrange
        service = DatasetService()
        csv_content = "name\tage\tactive\nAlice\t25\ttrue\nBob\t30\tfalse\n"
        csv_bytes = csv_content.encode('utf-8')

        # Act
        result = await service.import_csv(
            file_bytes=csv_bytes,
            name="Tab Delimited",
            owner_id="user_123",
            dynamodb=mock_dynamodb,
            s3_client=mock_s3_client,
            delimiter='\t',
        )

        # Assert
        assert result.row_count == 2
        assert result.column_count == 3

    @pytest.mark.asyncio
    async def test_import_csv_with_partition_column(
        self,
        sample_csv_bytes: bytes,
        mock_dynamodb: Any,
        mock_s3_client: Any,
    ) -> None:
        """Test CSV import with partitioning by column."""
        # Arrange
        service = DatasetService()

        # Act
        result = await service.import_csv(
            file_bytes=sample_csv_bytes,
            name="Partitioned Dataset",
            owner_id="user_123",
            dynamodb=mock_dynamodb,
            s3_client=mock_s3_client,
            partition_column='active',
        )

        # Assert
        assert result.partition_column == 'active'
        assert result.s3_path is not None
        assert 'partitions' in result.s3_path
        # Multiple partition files should be uploaded
        assert mock_s3_client.put_object.call_count >= 2

    @pytest.mark.asyncio
    async def test_import_csv_immutability(
        self,
        sample_csv_bytes: bytes,
        mock_dynamodb: Any,
        mock_s3_client: Any,
    ) -> None:
        """Test that import_csv doesn't mutate input parameters."""
        # Arrange
        service = DatasetService()
        original_bytes = sample_csv_bytes
        name = "Test Dataset"
        owner_id = "user_123"

        # Act
        await service.import_csv(
            file_bytes=sample_csv_bytes,
            name=name,
            owner_id=owner_id,
            dynamodb=mock_dynamodb,
            s3_client=mock_s3_client,
        )

        # Assert - original bytes unchanged
        assert sample_csv_bytes == original_bytes

    @pytest.mark.asyncio
    async def test_import_csv_empty_file(
        self,
        mock_dynamodb: Any,
        mock_s3_client: Any,
    ) -> None:
        """Test import_csv with empty CSV file."""
        # Arrange
        service = DatasetService()
        empty_bytes = b""

        # Act & Assert
        with pytest.raises(ValueError, match="CSV file is empty"):
            await service.import_csv(
                file_bytes=empty_bytes,
                name="Empty Dataset",
                owner_id="user_123",
                dynamodb=mock_dynamodb,
                s3_client=mock_s3_client,
            )

    @pytest.mark.asyncio
    async def test_import_csv_invalid_name(
        self,
        sample_csv_bytes: bytes,
        mock_dynamodb: Any,
        mock_s3_client: Any,
    ) -> None:
        """Test import_csv with empty name."""
        # Arrange
        service = DatasetService()

        # Act & Assert
        with pytest.raises(ValueError, match="name cannot be empty"):
            await service.import_csv(
                file_bytes=sample_csv_bytes,
                name="",
                owner_id="user_123",
                dynamodb=mock_dynamodb,
                s3_client=mock_s3_client,
            )

    @pytest.mark.asyncio
    async def test_import_csv_invalid_owner_id(
        self,
        sample_csv_bytes: bytes,
        mock_dynamodb: Any,
        mock_s3_client: Any,
    ) -> None:
        """Test import_csv with empty owner_id."""
        # Arrange
        service = DatasetService()

        # Act & Assert
        with pytest.raises(ValueError, match="owner_id cannot be empty"):
            await service.import_csv(
                file_bytes=sample_csv_bytes,
                name="Test Dataset",
                owner_id="",
                dynamodb=mock_dynamodb,
                s3_client=mock_s3_client,
            )


class TestDatasetServiceGetPreview:
    """Tests for get_preview method."""

    @pytest.mark.asyncio
    async def test_get_preview_success(
        self,
        mock_s3_client: Any,
    ) -> None:
        """Test get_preview returns correct preview structure."""
        # Arrange
        service = DatasetService()
        dataset = Dataset(
            id='ds_123456789abc',
            name='Test Dataset',
            source_type='csv',
            schema=[
                ColumnSchema(name='name', data_type='string', nullable=False),
                ColumnSchema(name='age', data_type='int64', nullable=False),
            ],
            s3_path='datasets/ds_123456789abc/data/part-0000.parquet',
            row_count=100,
            column_count=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Mock S3 to return parquet data
        sample_df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
        })

        with patch('app.services.dataset_service.ParquetReader') as mock_reader:
            mock_reader_instance = MagicMock()
            mock_reader.return_value = mock_reader_instance
            mock_reader_instance.read_preview.return_value = sample_df

            # Act
            result = await service.get_preview(
                dataset=dataset,
                s3_client=mock_s3_client,
                max_rows=100,
            )

        # Assert
        assert 'columns' in result
        assert 'rows' in result
        assert 'total_rows' in result
        assert 'preview_rows' in result

        assert result['columns'] == ['name', 'age']
        assert len(result['rows']) == 3
        assert result['total_rows'] == 100
        assert result['preview_rows'] == 3

    @pytest.mark.asyncio
    async def test_get_preview_custom_max_rows(
        self,
        mock_s3_client: Any,
    ) -> None:
        """Test get_preview with custom max_rows parameter."""
        # Arrange
        service = DatasetService()
        dataset = Dataset(
            id='ds_123456789abc',
            name='Test Dataset',
            source_type='csv',
            schema=[
                ColumnSchema(name='name', data_type='string', nullable=False),
            ],
            s3_path='datasets/ds_123456789abc/data/part-0000.parquet',
            row_count=1000,
            column_count=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Mock S3
        sample_df = pd.DataFrame({'name': [f'User{i}' for i in range(50)]})

        with patch('app.services.dataset_service.ParquetReader') as mock_reader:
            mock_reader_instance = MagicMock()
            mock_reader.return_value = mock_reader_instance
            mock_reader_instance.read_preview.return_value = sample_df

            # Act
            result = await service.get_preview(
                dataset=dataset,
                s3_client=mock_s3_client,
                max_rows=50,
            )

        # Assert
        assert result['preview_rows'] == 50

    @pytest.mark.asyncio
    async def test_get_preview_no_s3_path(
        self,
        mock_s3_client: Any,
    ) -> None:
        """Test get_preview when dataset has no s3_path."""
        # Arrange
        service = DatasetService()
        dataset = Dataset(
            id='ds_123456789abc',
            name='Test Dataset',
            source_type='csv',
            schema=[],
            s3_path=None,  # No S3 path
            row_count=0,
            column_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act
        result = await service.get_preview(
            dataset=dataset,
            s3_client=mock_s3_client,
        )

        # Assert - empty result
        assert result == {
            'columns': [],
            'rows': [],
            'total_rows': 0,
            'preview_rows': 0,
        }

    @pytest.mark.asyncio
    async def test_get_preview_max_rows_validation(
        self,
        mock_s3_client: Any,
    ) -> None:
        """Test get_preview validates max_rows parameter (1-1000)."""
        # Arrange
        service = DatasetService()
        dataset = Dataset(
            id='ds_123456789abc',
            name='Test Dataset',
            source_type='csv',
            schema=[],
            s3_path='datasets/ds_123456789abc/data/part-0000.parquet',
            row_count=100,
            column_count=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act & Assert - max_rows too small
        with pytest.raises(ValueError, match="max_rows must be between 1 and 1000"):
            await service.get_preview(dataset=dataset, s3_client=mock_s3_client, max_rows=0)

        # Act & Assert - max_rows too large
        with pytest.raises(ValueError, match="max_rows must be between 1 and 1000"):
            await service.get_preview(dataset=dataset, s3_client=mock_s3_client, max_rows=1001)

    @pytest.mark.asyncio
    async def test_get_preview_immutability(
        self,
        mock_s3_client: Any,
    ) -> None:
        """Test get_preview doesn't mutate dataset object."""
        # Arrange
        service = DatasetService()
        original_dataset = Dataset(
            id='ds_123456789abc',
            name='Test Dataset',
            source_type='csv',
            schema=[
                ColumnSchema(name='name', data_type='string', nullable=False),
            ],
            s3_path='datasets/ds_123456789abc/data/part-0000.parquet',
            row_count=100,
            column_count=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Store original values
        original_id = original_dataset.id
        original_name = original_dataset.name
        original_row_count = original_dataset.row_count

        # Mock S3
        sample_df = pd.DataFrame({'name': ['Alice', 'Bob']})

        with patch('app.services.dataset_service.ParquetReader') as mock_reader:
            mock_reader_instance = MagicMock()
            mock_reader.return_value = mock_reader_instance
            mock_reader_instance.read_preview.return_value = sample_df

            # Act
            await service.get_preview(
                dataset=original_dataset,
                s3_client=mock_s3_client,
            )

        # Assert - dataset unchanged
        assert original_dataset.id == original_id
        assert original_dataset.name == original_name
        assert original_dataset.row_count == original_row_count
