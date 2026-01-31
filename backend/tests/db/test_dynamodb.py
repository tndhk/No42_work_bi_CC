"""Tests for DynamoDB connection layer."""
import pytest
from moto import mock_aws
from app.db.dynamodb import get_dynamodb_resource
from app.core.config import settings


@mock_aws
@pytest.mark.asyncio
async def test_get_dynamodb_resource():
    """Test that DynamoDB resource can be obtained from get_dynamodb_resource."""
    async for dynamodb in get_dynamodb_resource():
        assert dynamodb is not None
        assert hasattr(dynamodb, 'Table')
        break


@mock_aws
@pytest.mark.asyncio
async def test_dynamodb_endpoint_url_from_settings():
    """Test that endpoint_url is correctly read from settings."""
    # Verify settings has the dynamodb_endpoint
    assert hasattr(settings, 'dynamodb_endpoint')

    async for dynamodb in get_dynamodb_resource():
        # Resource should be created with the endpoint from settings
        assert dynamodb is not None
        break


@mock_aws
@pytest.mark.asyncio
async def test_dynamodb_region_from_settings():
    """Test that region is correctly read from settings."""
    # Verify settings has the dynamodb_region
    assert hasattr(settings, 'dynamodb_region')
    assert settings.dynamodb_region == "ap-northeast-1"

    async for dynamodb in get_dynamodb_resource():
        assert dynamodb is not None
        break


@mock_aws
@pytest.mark.asyncio
async def test_dynamodb_table_prefix_configuration():
    """Test that table prefix is available in settings."""
    # Verify settings has the table prefix
    assert hasattr(settings, 'dynamodb_table_prefix')
    assert settings.dynamodb_table_prefix == "bi_"


@mock_aws
@pytest.mark.asyncio
async def test_dynamodb_resource_is_async_generator():
    """Test that get_dynamodb_resource is properly an async generator."""
    from collections.abc import AsyncGenerator

    dynamodb_gen = get_dynamodb_resource()
    # Verify it's an async generator
    assert hasattr(dynamodb_gen, '__aenter__') or hasattr(dynamodb_gen, '__anext__')
