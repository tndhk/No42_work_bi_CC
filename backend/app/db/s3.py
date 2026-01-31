"""S3 connection module using aioboto3."""
from typing import AsyncGenerator, Any
import os
import aioboto3

from app.core.config import settings


async def get_s3_client() -> AsyncGenerator[Any, None]:
    """Create and yield S3 client using aioboto3.

    Yields:
        aioboto3 S3 client

    Configuration is read from settings:
    - endpoint_url: Optional custom endpoint (for local development)
    - region_name: AWS region
    - aws_access_key_id: AWS access key (optional)
    - aws_secret_access_key: AWS secret key (optional)
    """
    # Use settings if available, fallback to environment variables
    access_key = settings.s3_access_key or os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = settings.s3_secret_key or os.environ.get('AWS_SECRET_ACCESS_KEY')

    session = aioboto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    async with session.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        region_name=settings.s3_region,
    ) as s3:
        yield s3
