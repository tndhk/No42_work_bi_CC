"""Dashboard API routes."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_dynamodb_resource
from app.models.dashboard import Dashboard, DashboardCreate, DashboardUpdate
from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("", response_model=list[Dashboard])
async def list_dashboards(
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> list[Dashboard]:
    """List all dashboards owned by current user.

    Args:
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        List of dashboards
    """
    repo = DashboardRepository()
    dashboards = await repo.list_by_owner(current_user.id, dynamodb)
    return dashboards


@router.post("", response_model=Dashboard, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> Dashboard:
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

    return dashboard


@router.get("/{dashboard_id}", response_model=Dashboard)
async def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> Dashboard:
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

    return dashboard


@router.put("/{dashboard_id}", response_model=Dashboard)
async def update_dashboard(
    dashboard_id: str,
    update_data: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> Dashboard:
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

    return updated_dashboard


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

    return referenced_datasets
