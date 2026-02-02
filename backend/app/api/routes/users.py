"""User API routes."""
from typing import Any
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_dynamodb_resource
from app.api.response import api_response
from app.models.user import User
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.get("")
async def search_users(
    q: str = Query("", description="Email search query"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Search users by email.

    Args:
        q: Search query (email partial match)
        limit: Maximum number of results
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        List of matching users (public fields only)
    """
    if not q or not q.strip():
        return api_response([])

    repo = UserRepository()
    users_in_db = await repo.scan_by_email_prefix(q.strip(), limit, dynamodb)

    # Convert to public User model (exclude hashed_password)
    users = [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
        }
        for u in users_in_db
    ]

    return api_response(users)
