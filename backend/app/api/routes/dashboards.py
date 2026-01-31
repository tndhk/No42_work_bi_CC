"""Dashboard API routes."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_dynamodb_resource
from app.api.response import api_response, paginated_response
from app.models.dashboard import Dashboard, DashboardCreate, DashboardUpdate
from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("")
async def list_dashboards(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """List all dashboards owned by current user.

    Args:
        limit: Maximum number of items to return (1-100, default: 50)
        offset: Number of items to skip (default: 0)
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Paginated list of dashboards
    """
    repo = DashboardRepository()
    all_dashboards = await repo.list_by_owner(current_user.id, dynamodb)

    # Apply pagination
    total = len(all_dashboards)
    dashboards = all_dashboards[offset:offset + limit]

    return paginated_response(
        items=[d.model_dump() for d in dashboards],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Create a new dashboard.

    Args:
        dashboard_data: Dashboard creation data
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Created dashboard

    Raises:
        HTTPException: 422 if validation fails
    """
    # Validate name
    if not dashboard_data.name or not dashboard_data.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty",
        )

    # Prepare creation data
    create_data = {
        'name': dashboard_data.name.strip(),
        'description': dashboard_data.description,
        'layout': dashboard_data.layout,
        'filters': dashboard_data.filters,
        'owner_id': current_user.id,
    }

    # Create dashboard
    repo = DashboardRepository()
    dashboard = await repo.create(create_data, dynamodb)

    return api_response(dashboard.model_dump())


@router.get("/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Get dashboard by ID.

    Args:
        dashboard_id: Dashboard ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Dashboard instance

    Raises:
        HTTPException: 404 if not found
    """
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    return api_response(dashboard.model_dump())


@router.put("/{dashboard_id}")
async def update_dashboard(
    dashboard_id: str,
    update_data: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Update dashboard.

    Args:
        dashboard_id: Dashboard ID
        update_data: Update fields
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Updated dashboard

    Raises:
        HTTPException: 403 if not owner, 404 if not found
    """
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    # Check ownership
    if dashboard.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this dashboard",
        )

    # Update dashboard
    update_dict = update_data.model_dump(exclude_unset=True)

    updated_dashboard = await repo.update(dashboard_id, update_dict, dynamodb)

    if not updated_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found after update",
        )

    return api_response(updated_dashboard.model_dump())


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> None:
    """Delete dashboard.

    Args:
        dashboard_id: Dashboard ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Raises:
        HTTPException: 403 if not owner, 404 if not found
    """
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    # Check ownership
    if dashboard.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this dashboard",
        )

    # Delete dashboard
    await repo.delete(dashboard_id, dynamodb)


@router.post("/{dashboard_id}/clone", status_code=status.HTTP_201_CREATED)
async def clone_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Clone an existing dashboard.

    Args:
        dashboard_id: Dashboard ID to clone
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Cloned dashboard

    Raises:
        HTTPException: 404 if source dashboard not found
    """
    repo = DashboardRepository()
    source_dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not source_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    # Create cloned dashboard with new name and owner
    clone_data = {
        'name': f"{source_dashboard.name} (Copy)",
        'description': source_dashboard.description,
        'layout': source_dashboard.layout,
        'filters': source_dashboard.filters,
        'owner_id': current_user.id,
    }

    cloned_dashboard = await repo.create(clone_data, dynamodb)

    return api_response(cloned_dashboard.model_dump())


@router.get("/{dashboard_id}/referenced-datasets")
async def get_referenced_datasets(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> list[dict[str, Any]]:
    """Get datasets referenced by dashboard cards.

    Args:
        dashboard_id: Dashboard ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        List of referenced datasets with usage information

    Raises:
        HTTPException: 404 if dashboard not found
    """
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    # Get referenced datasets via service
    service = DashboardService()
    referenced_datasets = await service.get_referenced_datasets(
        dashboard=dashboard,
        dynamodb=dynamodb
    )

    return api_response(referenced_datasets)
