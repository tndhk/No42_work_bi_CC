"""Tests for Parquet Storage Service."""
import io
import pytest
import pandas as pd
import pyarrow.parquet as pq
from moto import mock_aws
import boto3
from dataclasses import asdict

from app.core.config import settings
from app.services.parquet_storage import (
    ParquetConverter,
    ParquetReader,
    StorageResult,
)


@pytest.fixture
def s3_client():
    """Create mock S3 client."""
    with mock_aws():
        s3 = boto3.client('s3', region_name=settings.s3_region)
        s3.create_bucket(
            Bucket=settings.s3_bucket_datasets,
            CreateBucketConfiguration={'LocationConstraint': settings.s3_region}
        )
        yield s3


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame with various data types."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'salary': [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
        'department': ['Sales', 'Engineering', 'Sales', 'Engineering', 'HR']
    })


@pytest.fixture
def empty_dataframe():
    """Create empty DataFrame."""
    return pd.DataFrame({
        'id': pd.Series([], dtype='int64'),
        'name': pd.Series([], dtype='str'),
        'value': pd.Series([], dtype='float64')
    })


class TestStorageResult:
    """Test StorageResult dataclass."""

    def test_storage_result_is_immutable(self):
        """Test that StorageResult is immutable (frozen)."""
        result = StorageResult(
            s3_path='datasets/test/data/part-0000.parquet',
            partitioned=False,
            partition_column=None,
            partitions=[]
        )

        with pytest.raises(Exception):
            result.s3_path = 'new_path'

    def test_storage_result_to_dict(self):
        """Test StorageResult can be converted to dict."""
        result = StorageResult(
            s3_path='datasets/test/data/part-0000.parquet',
            partitioned=True,
            partition_column='department',
            partitions=['Sales', 'Engineering']
        )

        result_dict = asdict(result)
        assert result_dict['s3_path'] == 'datasets/test/data/part-0000.parquet'
        assert result_dict['partitioned'] is True
        assert result_dict['partition_column'] == 'department'
        assert result_dict['partitions'] == ['Sales', 'Engineering']


class TestParquetConverter:
    """Test ParquetConverter class."""

    def test_convert_and_save_non_partitioned(self, s3_client, sample_dataframe):
        """Test converting and saving DataFrame without partitioning."""
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-001'

        result = converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        assert result.partitioned is False
        assert result.partition_column is None
        assert result.partitions == []
        assert result.s3_path == f'datasets/{dataset_id}/data/part-0000.parquet'

        # Verify file exists in S3
        response = s3_client.list_objects_v2(
            Bucket=settings.s3_bucket_datasets,
            Prefix=f'datasets/{dataset_id}/data/'
        )
        assert 'Contents' in response
        assert len(response['Contents']) == 1

    def test_convert_and_save_partitioned(self, s3_client, sample_dataframe):
        """Test converting and saving DataFrame with partitioning."""
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-002'

        result = converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column='department'
        )

        assert result.partitioned is True
        assert result.partition_column == 'department'
        assert set(result.partitions) == {'Sales', 'Engineering', 'HR'}
        assert result.s3_path.startswith(f'datasets/{dataset_id}/partitions/')

        # Verify partition files exist in S3
        response = s3_client.list_objects_v2(
            Bucket=settings.s3_bucket_datasets,
            Prefix=f'datasets/{dataset_id}/partitions/'
        )
        assert 'Contents' in response
        assert len(response['Contents']) == 3  # 3 departments

    def test_s3_path_format_non_partitioned(self, s3_client, sample_dataframe):
        """Test S3 path format for non-partitioned data."""
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-003'

        result = converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        expected_path = f'datasets/{dataset_id}/data/part-0000.parquet'
        assert result.s3_path == expected_path

    def test_s3_path_format_partitioned(self, s3_client, sample_dataframe):
        """Test S3 path format for partitioned data."""
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-004'

        converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column='department'
        )

        # Check that partition paths contain department values
        response = s3_client.list_objects_v2(
            Bucket=settings.s3_bucket_datasets,
            Prefix=f'datasets/{dataset_id}/partitions/'
        )

        keys = [obj['Key'] for obj in response['Contents']]
        assert any('department=Sales' in key for key in keys)
        assert any('department=Engineering' in key for key in keys)
        assert any('department=HR' in key for key in keys)

    def test_compression_snappy(self, s3_client, sample_dataframe):
        """Test that files are compressed with snappy."""
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-005'

        converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        # Read file from S3 and check compression
        s3_key = f'datasets/{dataset_id}/data/part-0000.parquet'
        response = s3_client.get_object(
            Bucket=settings.s3_bucket_datasets,
            Key=s3_key
        )
        parquet_data = response['Body'].read()

        # Read parquet metadata
        parquet_file = pq.ParquetFile(io.BytesIO(parquet_data))
        metadata = parquet_file.metadata
        assert metadata.row_group(0).column(0).compression == 'SNAPPY'

    def test_empty_dataframe(self, s3_client, empty_dataframe):
        """Test handling of empty DataFrame."""
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-006'

        result = converter.convert_and_save(
            df=empty_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        assert result.partitioned is False
        assert result.s3_path == f'datasets/{dataset_id}/data/part-0000.parquet'

        # Verify file exists
        response = s3_client.head_object(
            Bucket=settings.s3_bucket_datasets,
            Key=result.s3_path
        )
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200

    def test_data_type_preservation(self, s3_client, sample_dataframe):
        """Test that data types are preserved correctly."""
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-007'

        converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        # Read back and verify types
        reader = ParquetReader(s3_client, settings.s3_bucket_datasets)
        s3_path = f'datasets/{dataset_id}/data/part-0000.parquet'
        df_read = reader.read_full(s3_path)

        assert df_read['id'].dtype == 'int64'
        assert df_read['name'].dtype == 'object'  # string
        assert df_read['age'].dtype == 'int64'
        assert df_read['salary'].dtype == 'float64'


class TestParquetReader:
    """Test ParquetReader class."""

    def test_read_full_non_partitioned(self, s3_client, sample_dataframe):
        """Test reading full non-partitioned dataset."""
        # First save data
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-008'
        result = converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        # Read back
        reader = ParquetReader(s3_client, settings.s3_bucket_datasets)
        df_read = reader.read_full(result.s3_path)

        pd.testing.assert_frame_equal(df_read, sample_dataframe)

    def test_read_full_partitioned(self, s3_client, sample_dataframe):
        """Test reading full partitioned dataset."""
        # First save data
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-009'
        converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column='department'
        )

        # Read back
        reader = ParquetReader(s3_client, settings.s3_bucket_datasets)
        # For partitioned data, read_full should handle the base path
        base_path = f'datasets/{dataset_id}/partitions/'
        df_read = reader.read_full(base_path)

        # Sort both dataframes for comparison (partition order may differ)
        df_read_sorted = df_read.sort_values('id').reset_index(drop=True)
        df_expected_sorted = sample_dataframe.sort_values('id').reset_index(drop=True)

        pd.testing.assert_frame_equal(df_read_sorted, df_expected_sorted)

    def test_read_preview_limits_rows(self, s3_client, sample_dataframe):
        """Test read_preview returns limited rows."""
        # First save data
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-010'
        result = converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        # Read preview
        reader = ParquetReader(s3_client, settings.s3_bucket_datasets)
        df_preview = reader.read_preview(result.s3_path, max_rows=3)

        assert len(df_preview) == 3
        pd.testing.assert_frame_equal(
            df_preview,
            sample_dataframe.head(3)
        )

    def test_read_preview_max_rows_exceeds_total(self, s3_client, sample_dataframe):
        """Test read_preview when max_rows exceeds total rows."""
        # First save data
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-011'
        result = converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        # Read preview with large max_rows
        reader = ParquetReader(s3_client, settings.s3_bucket_datasets)
        df_preview = reader.read_preview(result.s3_path, max_rows=1000)

        assert len(df_preview) == len(sample_dataframe)
        pd.testing.assert_frame_equal(df_preview, sample_dataframe)

    def test_roundtrip_preserves_data(self, s3_client, sample_dataframe):
        """Test complete roundtrip: convert, save, read back."""
        converter = ParquetConverter(s3_client, settings.s3_bucket_datasets)
        reader = ParquetReader(s3_client, settings.s3_bucket_datasets)
        dataset_id = 'test-dataset-012'

        # Save
        result = converter.convert_and_save(
            df=sample_dataframe,
            dataset_id=dataset_id,
            partition_column=None
        )

        # Read full
        df_full = reader.read_full(result.s3_path)
        pd.testing.assert_frame_equal(df_full, sample_dataframe)

        # Read preview
        df_preview = reader.read_preview(result.s3_path, max_rows=2)
        pd.testing.assert_frame_equal(
            df_preview,
            sample_dataframe.head(2)
        )
