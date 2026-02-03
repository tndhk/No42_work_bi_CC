"""FilterView detail API routes (independent)."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_dynamodb_resource
from app.api.response import api_response
from app.models.dashboard_share import Permission
from app.models.filter_view import FilterViewUpdate
from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.filter_view_repository import FilterViewRepository
from app.services.permission_service import PermissionService

router = APIRouter()


@router.get("/{filter_view_id}")
async def get_filter_view(
    filter_view_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Get filter view by ID.

    Visibility rules:
    - Owner can always see their own filter views (regardless of is_shared)
    - Other users can see shared views (is_shared=True) if they have VIEWER permission on dashboard
    - Other users cannot see private views (is_shared=False)

    Args:
        filter_view_id: Filter view ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Filter view instance

    Raises:
        HTTPException: 404 if not found, 403 if not authorized
    """
    # 1. FilterViewが存在するか確認
    repo = FilterViewRepository()
    filter_view = await repo.get_by_id(filter_view_id, dynamodb)

    if not filter_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter view not found",
        )

    # 2. 自分がownerなら常に可視（Dashboard権限チェック不要）
    if filter_view.owner_id == current_user.id:
        return api_response(filter_view.model_dump())

    # 3. 自分がownerでない + is_shared=False → 不可視（403）
    if not filter_view.is_shared:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this filter view",
        )

    # 4. 自分がownerでない + is_shared=True → Dashboard権限チェック
    dash_repo = DashboardRepository()
    dashboard = await dash_repo.get_by_id(filter_view.dashboard_id, dynamodb)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    permission_service = PermissionService()
    await permission_service.assert_permission(
        dashboard, current_user.id, Permission.VIEWER, dynamodb
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

    Permission requirements:
    - Only owner can update filter view
    - Changing is_shared attribute requires EDITOR permission on dashboard

    Args:
        filter_view_id: Filter view ID
        update_data: Update fields
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Updated filter view

    Raises:
        HTTPException: 403 if not owner or insufficient permission, 404 if not found
    """
    repo = FilterViewRepository()
    filter_view = await repo.get_by_id(filter_view_id, dynamodb)

    if not filter_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter view not found",
        )

    # Only owner can update filter view
    if filter_view.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this filter view",
        )

    update_dict = update_data.model_dump(exclude_unset=True)

    # Check if is_shared is being changed - requires EDITOR permission
    if 'is_shared' in update_dict and update_dict['is_shared'] != filter_view.is_shared:
        dash_repo = DashboardRepository()
        dashboard = await dash_repo.get_by_id(filter_view.dashboard_id, dynamodb)
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found",
            )
        permission_service = PermissionService()
        await permission_service.assert_permission(
            dashboard, current_user.id, Permission.EDITOR, dynamodb
        )

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
