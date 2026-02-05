"""Authentication API routes."""
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from app.api.deps import get_current_user_401, get_dynamodb_resource
from app.api.response import api_response
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
# Disable rate limiting if configured (e.g., for E2E tests)
limiter.enabled = settings.rate_limit_enabled
logger = structlog.get_logger(__name__)


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest = Body(...),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Authenticate user and return access token.

    Rate limit: 5 requests per minute per IP address.

    Args:
        request: HTTP request object (for rate limiting)
        login_data: Login credentials
        dynamodb: DynamoDB resource

    Returns:
        Access token, token type, expires_in (seconds), and user info

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Retrieve user by email
    repo = UserRepository()
    user = await repo.get_by_email(login_data.email, dynamodb)

    audit = AuditService()

    if not user:
        logger.warning(
            "login_failed",
            email=login_data.email,
            reason="user_not_found",
            ip=get_remote_address(request)
        )
        await audit.log_user_login_failed(
            email=login_data.email, reason="user_not_found", dynamodb=dynamodb
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        logger.warning(
            "login_failed",
            email=login_data.email,
            user_id=user.id,
            reason="invalid_password",
            ip=get_remote_address(request)
        )
        await audit.log_user_login_failed(
            email=login_data.email, reason="invalid_password", dynamodb=dynamodb
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    expires_in = settings.jwt_expiration_hours * 3600

    logger.info(
        "login_success",
        email=login_data.email,
        user_id=user.id,
        ip=get_remote_address(request)
    )

    await audit.log_user_login(user_id=user.id, dynamodb=dynamodb)

    return api_response({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "user_id": user.id,
            "email": user.email,
        }
    })


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user_401),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Logout current user.

    Note: This is a stateless JWT-based auth system.
    Logout is handled client-side by removing the token.

    Args:
        current_user: Current authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Success message
    """
    audit = AuditService()
    await audit.log_user_logout(user_id=current_user.id, dynamodb=dynamodb)
    return api_response({"message": "Successfully logged out"})


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user_401),
) -> dict[str, Any]:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information (excludes sensitive fields)
    """
    return api_response({
        "user_id": current_user.id,
        "email": current_user.email,
    })
