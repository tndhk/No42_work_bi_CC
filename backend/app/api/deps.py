"""API dependencies for authentication and resource injection."""
from typing import Any, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.models.user import User

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_dynamodb_resource() -> AsyncGenerator[Any, None]:
    """Get DynamoDB resource using aioboto3.

    Yields:
        DynamoDB resource from aioboto3
    """
    import aioboto3

    session = aioboto3.Session()
    async with session.resource(
        'dynamodb',
        region_name=settings.dynamodb_region,
        endpoint_url=settings.dynamodb_endpoint,
    ) as dynamodb:
        yield dynamodb


async def get_s3_client() -> AsyncGenerator[Any, None]:
    """Get S3 client using aioboto3.

    Yields:
        S3 client from aioboto3
    """
    import aioboto3

    session = aioboto3.Session()

    async with session.client(
        's3',
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint if settings.s3_endpoint else None,
        aws_access_key_id=settings.s3_access_key if settings.s3_access_key and settings.s3_secret_key else None,
        aws_secret_access_key=settings.s3_secret_key if settings.s3_access_key and settings.s3_secret_key else None,
    ) as s3:
        yield s3


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        dynamodb: DynamoDB resource

    Returns:
        Current authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    # Extract token from credentials
    token = credentials.credentials

    # Decode and verify token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Extract user ID from token payload
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Retrieve user from database
    repo = UserRepository()
    user_in_db = await repo.get_by_id(user_id, dynamodb)

    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Convert to public User model (excludes hashed_password)
    user = User(
        id=user_in_db.id,
        email=user_in_db.email,
        created_at=user_in_db.created_at,
        updated_at=user_in_db.updated_at,
    )

    return user
