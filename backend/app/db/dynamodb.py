"""DynamoDB connection module using aioboto3."""
from typing import AsyncGenerator, Any
import aioboto3

from app.core.config import settings


async def get_dynamodb_resource() -> AsyncGenerator[Any, None]:
    """Create and yield DynamoDB resource using aioboto3.

    Yields:
        aioboto3 DynamoDB resource

    Configuration is read from settings:
    - endpoint_url: Optional custom endpoint (for local development)
    - region_name: AWS region
    """
    session = aioboto3.Session()
    async with session.resource(
        "dynamodb",
        endpoint_url=settings.dynamodb_endpoint,
        region_name=settings.dynamodb_region,
    ) as dynamodb:
        yield dynamodb
