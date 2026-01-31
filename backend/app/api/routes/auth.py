"""Authentication API routes."""
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from app.api.deps import get_current_user, get_dynamodb_resource
from app.core.security import verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.models.user import User

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
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


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest = Body(...),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> LoginResponse:
    """Authenticate user and return access token.

    Rate limit: 5 requests per minute per IP address.

    Args:
        request: HTTP request object (for rate limiting)
        login_data: Login credentials
        dynamodb: DynamoDB resource

    Returns:
        Access token and token type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Retrieve user by email
    repo = UserRepository()
    user = await repo.get_by_email(login_data.email, dynamodb)

    if not user:
        logger.warning(
            "login_failed",
            email=login_data.email,
            reason="user_not_found",
            ip=get_remote_address(request)
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    logger.info(
        "login_success",
        email=login_data.email,
        user_id=user.id,
        ip=get_remote_address(request)
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Logout current user.

    Note: This is a stateless JWT-based auth system.
    Logout is handled client-side by removing the token.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=User)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information (excludes sensitive fields)
    """
    return current_user
