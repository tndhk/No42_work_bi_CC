"""FilterView detail API routes (independent)."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_dynamodb_resource
from app.api.response import api_response
from app.models.filter_view import FilterViewUpdate
from app.models.user import User
from app.repositories.filter_view_repository import FilterViewRepository

router = APIRouter()


@router.get("/{filter_view_id}")
async def get_filter_view(
    filter_view_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Get filter view by ID.

    Args:
        filter_view_id: Filter view ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Filter view instance

    Raises:
        HTTPException: 404 if not found
    """
    repo = FilterViewRepository()
    filter_view = await repo.get_by_id(filter_view_id, dynamodb)

    if not filter_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter view not found",
        )

    return api_response(filter_view.model_dump())


@router.put("/{filter_view_id}")
async def update_filter_view(
    filter_view_id: str,
    update_data: FilterViewUpdate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Update filter view.

    Args:
        filter_view_id: Filter view ID
        update_data: Update fields
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Updated filter view

    Raises:
        HTTPException: 403 if not owner, 404 if not found
    """
    repo = FilterViewRepository()
    filter_view = await repo.get_by_id(filter_view_id, dynamodb)

    if not filter_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter view not found",
        )

    if filter_view.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this filter view",
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    updated_filter_view = await repo.update(filter_view_id, update_dict, dynamodb)

    if not updated_filter_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter view not found after update",
        )

    return api_response(updated_filter_view.model_dump())


@router.delete("/{filter_view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter_view(
    filter_view_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> None:
    """Delete filter view.

    Args:
        filter_view_id: Filter view ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Raises:
        HTTPException: 403 if not owner, 404 if not found
    """
    repo = FilterViewRepository()
    filter_view = await repo.get_by_id(filter_view_id, dynamodb)

    if not filter_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter view not found",
        )

    if filter_view.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this filter view",
        )

    await repo.delete(filter_view_id, dynamodb)
