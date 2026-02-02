"""Tests for S3ImportRequest model."""
import pytest
from pydantic import ValidationError

from app.models.dataset import S3ImportRequest


class TestS3ImportRequest:
    """Tests for S3ImportRequest model."""

    def test_valid_minimal(self):
        """Test creating S3ImportRequest with required fields only."""
        req = S3ImportRequest(
            name="test-dataset",
            s3_bucket="my-bucket",
            s3_key="data/file.csv",
        )
        assert req.name == "test-dataset"
        assert req.s3_bucket == "my-bucket"
        assert req.s3_key == "data/file.csv"
        assert req.has_header is True
        assert req.delimiter == ","
        assert req.encoding is None
        assert req.partition_column is None

    def test_valid_all_fields(self):
        """Test creating S3ImportRequest with all fields."""
        req = S3ImportRequest(
            name="full-dataset",
            s3_bucket="my-bucket",
            s3_key="data/file.csv",
            has_header=False,
            delimiter="\t",
            encoding="utf-8",
            partition_column="date",
        )
        assert req.name == "full-dataset"
        assert req.has_header is False
        assert req.delimiter == "\t"
        assert req.encoding == "utf-8"
        assert req.partition_column == "date"

    def test_empty_name_fails(self):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError):
            S3ImportRequest(
                name="",
                s3_bucket="my-bucket",
                s3_key="data/file.csv",
            )

    def test_whitespace_name_fails(self):
        """Test that whitespace-only name raises ValidationError."""
        with pytest.raises(ValidationError):
            S3ImportRequest(
                name="   ",
                s3_bucket="my-bucket",
                s3_key="data/file.csv",
            )

    def test_missing_name_fails(self):
        """Test that missing name raises ValidationError."""
        with pytest.raises(ValidationError):
            S3ImportRequest(
                s3_bucket="my-bucket",
                s3_key="data/file.csv",
            )

    def test_missing_s3_bucket_fails(self):
        """Test that missing s3_bucket raises ValidationError."""
        with pytest.raises(ValidationError):
            S3ImportRequest(
                name="test",
                s3_key="data/file.csv",
            )

    def test_missing_s3_key_fails(self):
        """Test that missing s3_key raises ValidationError."""
        with pytest.raises(ValidationError):
            S3ImportRequest(
                name="test",
                s3_bucket="my-bucket",
            )

    def test_empty_s3_bucket_fails(self):
        """Test that empty s3_bucket raises ValidationError."""
        with pytest.raises(ValidationError):
            S3ImportRequest(
                name="test",
                s3_bucket="",
                s3_key="data/file.csv",
            )

    def test_empty_s3_key_fails(self):
        """Test that empty s3_key raises ValidationError."""
        with pytest.raises(ValidationError):
            S3ImportRequest(
                name="test",
                s3_bucket="my-bucket",
                s3_key="",
            )
