"""FilterView API routes (dashboard-scoped)."""
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_dynamodb_resource
from app.api.response import api_response
from app.models.filter_view import FilterViewCreate
from app.models.user import User
from app.repositories.filter_view_repository import FilterViewRepository

router = APIRouter()


@router.get("")
async def list_filter_views(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """List all filter views for a dashboard.

    Args:
        dashboard_id: Dashboard ID from URL path
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        List of filter views for the dashboard
    """
    repo = FilterViewRepository()
    filter_views = await repo.list_by_dashboard(dashboard_id, dynamodb)
    return api_response([fv.model_dump() for fv in filter_views])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_filter_view(
    dashboard_id: str,
    filter_view_data: FilterViewCreate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Create a new filter view for a dashboard.

    Args:
        dashboard_id: Dashboard ID from URL path
        filter_view_data: Filter view creation data
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Created filter view

    Raises:
        HTTPException: 422 if validation fails
    """
    create_data = {
        'id': f"fv_{uuid.uuid4().hex[:12]}",
        'dashboard_id': dashboard_id,
        'name': filter_view_data.name.strip(),
        'owner_id': current_user.id,
        'filter_state': filter_view_data.filter_state,
        'is_shared': filter_view_data.is_shared,
        'is_default': filter_view_data.is_default,
    }

    repo = FilterViewRepository()
    filter_view = await repo.create(create_data, dynamodb)

    return api_response(filter_view.model_dump())
