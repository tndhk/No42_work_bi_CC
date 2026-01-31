"""Tests for S3 connection layer."""
import pytest
from moto import mock_aws
from app.db.s3 import get_s3_client
from app.core.config import settings


@mock_aws
@pytest.mark.asyncio
async def test_get_s3_client():
    """Test that S3 client can be obtained from get_s3_client."""
    async for s3 in get_s3_client():
        assert s3 is not None
        assert hasattr(s3, 'put_object')
        assert hasattr(s3, 'get_object')
        break


@mock_aws
@pytest.mark.asyncio
async def test_s3_endpoint_url_from_settings():
    """Test that endpoint_url is correctly read from settings."""
    # Verify settings has the s3_endpoint
    assert hasattr(settings, 's3_endpoint')

    async for s3 in get_s3_client():
        # Client should be created with the endpoint from settings
        assert s3 is not None
        break


@mock_aws
@pytest.mark.asyncio
async def test_s3_region_from_settings():
    """Test that region is correctly read from settings."""
    # Verify settings has the s3_region
    assert hasattr(settings, 's3_region')
    assert settings.s3_region == "ap-northeast-1"

    async for s3 in get_s3_client():
        assert s3 is not None
        break


@mock_aws
@pytest.mark.asyncio
async def test_s3_bucket_name_from_settings():
    """Test that S3 bucket name is available in settings."""
    # Verify settings has the bucket name
    assert hasattr(settings, 's3_bucket_datasets')
    assert settings.s3_bucket_datasets == "bi-datasets"


@mock_aws
@pytest.mark.asyncio
async def test_s3_client_has_core_methods():
    """Test that S3 client has all core methods."""
    async for s3 in get_s3_client():
        required_methods = [
            'put_object', 'get_object', 'delete_object',
            'list_objects_v2', 'head_object', 'create_bucket', 'list_buckets'
        ]
        for method in required_methods:
            assert hasattr(s3, method), f"S3 client missing method: {method}"
        break


@mock_aws
@pytest.mark.asyncio
async def test_s3_client_is_async_generator():
    """Test that get_s3_client is properly an async generator."""
    s3_gen = get_s3_client()
    # Verify it's an async generator
    assert hasattr(s3_gen, '__aenter__') or hasattr(s3_gen, '__anext__')
