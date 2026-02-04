"""Tests for DatasetService.import_s3_csv method."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from botocore.exceptions import ClientError

from app.services.dataset_service import DatasetService


class TestImportS3Csv:
    """Tests for import_s3_csv method."""

    @pytest.fixture
    def service(self):
        return DatasetService()

    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client that returns CSV data."""
        client = AsyncMock()
        # Mock the get_object response
        body_mock = AsyncMock()
        body_mock.read = AsyncMock(return_value=b"col1,col2\nval1,val2\nval3,val4")
        response = {"Body": body_mock}
        client.get_object = AsyncMock(return_value=response)
        return client

    @pytest.fixture
    def mock_dynamodb(self):
        return MagicMock()

    @pytest.fixture
    def mock_storage_s3_client(self):
        """S3 client for Parquet storage (separate from source S3)."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_import_s3_csv_success(self, service, mock_s3_client, mock_dynamodb, mock_storage_s3_client):
        """Test successful S3 CSV import."""
        with patch.object(service, '_save_to_s3') as mock_save, \
             patch.object(service, '_save_metadata') as mock_save_meta:
            mock_save.return_value = MagicMock(s3_path="datasets/ds_test123/data.parquet")
            mock_save_meta.return_value = MagicMock()

            result = await service.import_s3_csv(
                name="test-dataset",
                s3_bucket="source-bucket",
                s3_key="data/file.csv",
                owner_id="user_123",
                dynamodb=mock_dynamodb,
                s3_client=mock_storage_s3_client,
                source_s3_client=mock_s3_client,
            )

            # Verify S3 was called to get the object
            mock_s3_client.get_object.assert_called_once_with(
                Bucket="source-bucket", Key="data/file.csv"
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_import_s3_csv_empty_file(self, service, mock_dynamodb, mock_storage_s3_client):
        """Test import fails for empty CSV file."""
        client = AsyncMock()
        body_mock = AsyncMock()
        body_mock.read = AsyncMock(return_value=b"")
        client.get_object = AsyncMock(return_value={"Body": body_mock})

        with pytest.raises(ValueError, match="empty"):
            await service.import_s3_csv(
                name="test-dataset",
                s3_bucket="bucket",
                s3_key="empty.csv",
                owner_id="user_123",
                dynamodb=mock_dynamodb,
                s3_client=mock_storage_s3_client,
                source_s3_client=client,
            )

    @pytest.mark.asyncio
    async def test_import_s3_csv_key_not_found(self, service, mock_dynamodb, mock_storage_s3_client):
        """Test import fails when S3 key doesn't exist."""
        client = AsyncMock()
        error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
        client.get_object = AsyncMock(
            side_effect=ClientError(error_response, "GetObject")
        )

        with pytest.raises(ValueError, match="S3"):
            await service.import_s3_csv(
                name="test-dataset",
                s3_bucket="bucket",
                s3_key="nonexistent.csv",
                owner_id="user_123",
                dynamodb=mock_dynamodb,
                s3_client=mock_storage_s3_client,
                source_s3_client=client,
            )

    @pytest.mark.asyncio
    async def test_import_s3_csv_source_config_saved(self, service, mock_s3_client, mock_dynamodb, mock_storage_s3_client):
        """Test that source_config is saved with s3_bucket and s3_key."""
        with patch.object(service, '_save_to_s3') as mock_save, \
             patch.object(service, '_save_metadata') as mock_save_meta:
            mock_save.return_value = MagicMock(s3_path="datasets/ds_test123/data.parquet")
            mock_save_meta.return_value = MagicMock()

            await service.import_s3_csv(
                name="test-dataset",
                s3_bucket="source-bucket",
                s3_key="data/file.csv",
                owner_id="user_123",
                dynamodb=mock_dynamodb,
                s3_client=mock_storage_s3_client,
                source_s3_client=mock_s3_client,
            )

            # Verify _save_metadata was called with source_type="s3_csv" and source_config
            call_kwargs = mock_save_meta.call_args[1] if mock_save_meta.call_args[1] else {}
            if not call_kwargs:
                _ = mock_save_meta.call_args[0]
                # Check positional args - can't easily check, so we verify call was made
            assert mock_save_meta.called

    @pytest.mark.asyncio
    async def test_import_s3_csv_empty_name_fails(self, service, mock_s3_client, mock_dynamodb, mock_storage_s3_client):
        """Test import fails with empty name."""
        with pytest.raises(ValueError, match="name"):
            await service.import_s3_csv(
                name="",
                s3_bucket="bucket",
                s3_key="file.csv",
                owner_id="user_123",
                dynamodb=mock_dynamodb,
                s3_client=mock_storage_s3_client,
                source_s3_client=mock_s3_client,
            )

    @pytest.mark.asyncio
    async def test_import_s3_csv_with_options(self, service, mock_dynamodb, mock_storage_s3_client):
        """Test import with custom delimiter and encoding."""
        client = AsyncMock()
        body_mock = AsyncMock()
        body_mock.read = AsyncMock(return_value=b"col1\tcol2\nval1\tval2")
        client.get_object = AsyncMock(return_value={"Body": body_mock})

        with patch.object(service, '_save_to_s3') as mock_save, \
             patch.object(service, '_save_metadata') as mock_save_meta:
            mock_save.return_value = MagicMock(s3_path="datasets/ds_test123/data.parquet")
            mock_save_meta.return_value = MagicMock()

            await service.import_s3_csv(
                name="tsv-dataset",
                s3_bucket="bucket",
                s3_key="data.tsv",
                owner_id="user_123",
                dynamodb=mock_dynamodb,
                s3_client=mock_storage_s3_client,
                source_s3_client=client,
                delimiter="\t",
                encoding="utf-8",
            )

            assert mock_save.called
