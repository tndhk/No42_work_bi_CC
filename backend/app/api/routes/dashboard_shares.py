"""Dashboard Share API routes."""
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_dynamodb_resource
from app.api.response import api_response
from app.models.user import User
from app.models.dashboard_share import DashboardShareCreate, DashboardShareUpdate
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.dashboard_share_repository import DashboardShareRepository

router = APIRouter()


async def _get_dashboard_as_owner(dashboard_id: str, current_user: User, dynamodb: Any):
    """Helper: get dashboard and verify ownership.

    Args:
        dashboard_id: Dashboard ID to look up
        current_user: Currently authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Dashboard instance if found and owned by current user

    Raises:
        HTTPException: 404 if dashboard not found, 403 if not owner
    """
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )
    if dashboard.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only dashboard owner can manage shares",
        )
    return dashboard


@router.get("")
async def list_shares(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """List all shares for a dashboard.

    Only the dashboard owner can view shares.

    Args:
        dashboard_id: Dashboard ID from URL path
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        List of dashboard shares
    """
    await _get_dashboard_as_owner(dashboard_id, current_user, dynamodb)
    share_repo = DashboardShareRepository()
    shares = await share_repo.list_by_dashboard(dashboard_id, dynamodb)
    return api_response([s.model_dump() for s in shares])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_share(
    dashboard_id: str,
    share_data: DashboardShareCreate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Create a new share for a dashboard.

    Only the dashboard owner can create shares. Duplicate shares
    (same dashboard + shared_to_type + shared_to_id) are rejected with 409.

    Args:
        dashboard_id: Dashboard ID from URL path
        share_data: Share creation data
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Created dashboard share
    """
    await _get_dashboard_as_owner(dashboard_id, current_user, dynamodb)

    share_repo = DashboardShareRepository()
    existing = await share_repo.find_share(
        dashboard_id,
        share_data.shared_to_type.value,
        share_data.shared_to_id,
        dynamodb,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Share already exists",
        )

    create_data = {
        'id': f"share_{uuid.uuid4().hex[:12]}",
        'dashboard_id': dashboard_id,
        'shared_to_type': share_data.shared_to_type.value,
        'shared_to_id': share_data.shared_to_id,
        'permission': share_data.permission.value,
        'shared_by': current_user.id,
    }
    share = await share_repo.create(create_data, dynamodb)
    return api_response(share.model_dump())


@router.put("/{share_id}")
async def update_share(
    dashboard_id: str,
    share_id: str,
    update_data: DashboardShareUpdate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Update a share's permission level.

    Only the dashboard owner can update shares.

    Args:
        dashboard_id: Dashboard ID from URL path
        share_id: Share ID from URL path
        update_data: Share update data (permission)
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Updated dashboard share
    """
    await _get_dashboard_as_owner(dashboard_id, current_user, dynamodb)

    share_repo = DashboardShareRepository()
    share = await share_repo.get_by_id(share_id, dynamodb)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found",
        )

    updated = await share_repo.update(
        share_id,
        {"permission": update_data.permission.value},
        dynamodb,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found after update",
        )
    return api_response(updated.model_dump())


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share(
    dashboard_id: str,
    share_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> None:
    """Delete a share from a dashboard.

    Only the dashboard owner can delete shares.

    Args:
        dashboard_id: Dashboard ID from URL path
        share_id: Share ID from URL path
        current_user: Authenticated user
        dynamodb: DynamoDB resource
    """
    await _get_dashboard_as_owner(dashboard_id, current_user, dynamodb)

    share_repo = DashboardShareRepository()
    share = await share_repo.get_by_id(share_id, dynamodb)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found",
        )
    await share_repo.delete(share_id, dynamodb)
