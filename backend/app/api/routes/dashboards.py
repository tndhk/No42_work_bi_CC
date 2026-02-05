"""Dashboard API routes."""
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_dynamodb_resource
from app.api.response import api_response, paginated_response
from app.models.dashboard import Dashboard, DashboardCreate, DashboardUpdate
from app.models.dashboard_share import Permission
from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.dashboard_share_repository import DashboardShareRepository
from app.repositories.group_member_repository import GroupMemberRepository
from app.repositories.user_repository import UserRepository
from app.services.dashboard_service import DashboardService
from app.services.permission_service import PERMISSION_LEVELS, PermissionService

router = APIRouter()


def _to_dashboard_response(dashboard_dict: dict) -> dict:
    """Convert dashboard dict to frontend-expected format (id -> dashboard_id)."""
    result = {**dashboard_dict}
    if 'id' in result:
        result['dashboard_id'] = result['id']
    return result


async def _process_shares(shares, repo, dashboard_map, permission_map, dynamodb):
    """Process a list of shares and update dashboard/permission maps."""
    for share in shares:
        perm_value = share.permission.value if isinstance(share.permission, Permission) else share.permission
        if share.dashboard_id not in dashboard_map:
            dash = await repo.get_by_id(share.dashboard_id, dynamodb)
            if dash:
                dashboard_map[dash.id] = dash
                permission_map[dash.id] = perm_value
        else:
            current_perm = permission_map[share.dashboard_id]
            current_level = PERMISSION_LEVELS.get(Permission(current_perm), 0)
            share_perm = share.permission if isinstance(share.permission, Permission) else Permission(share.permission)
            new_level = PERMISSION_LEVELS.get(share_perm, 0)
            if new_level > current_level:
                permission_map[share.dashboard_id] = share_perm.value


@router.get("")
async def list_dashboards(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """List all dashboards accessible by current user.

    Includes owned dashboards and shared dashboards (direct user shares
    and group shares). Each dashboard includes a `my_permission` field.

    Args:
        limit: Maximum number of items to return (1-100, default: 50)
        offset: Number of items to skip (default: 0)
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Paginated list of dashboards with my_permission
    """
    repo = DashboardRepository()

    # 1. Own dashboards
    own_dashboards = await repo.list_by_owner(current_user.id, dynamodb)
    dashboard_map: dict[str, Dashboard] = {d.id: d for d in own_dashboards}
    permission_map: dict[str, str] = {d.id: Permission.OWNER.value for d in own_dashboards}

    # 2. Direct user shares
    share_repo = DashboardShareRepository()
    user_shares = await share_repo.list_by_target(current_user.id, dynamodb)
    await _process_shares(user_shares, repo, dashboard_map, permission_map, dynamodb)

    # 3. Group shares
    member_repo = GroupMemberRepository()
    user_groups = await member_repo.list_groups_for_user(current_user.id, dynamodb)
    for group_id in user_groups:
        group_shares = await share_repo.list_by_target(group_id, dynamodb)
        await _process_shares(group_shares, repo, dashboard_map, permission_map, dynamodb)

    # 4. Merge and paginate
    all_dashboards = list(dashboard_map.values())
    all_dashboards.sort(key=lambda d: d.created_at, reverse=True)

    total = len(all_dashboards)
    page = all_dashboards[offset:offset + limit]

    # 5. Collect unique owner IDs and fetch user info
    user_repo = UserRepository()
    owner_ids = {d.owner_id for d in page if d.owner_id}
    owner_map: dict[str, str] = {}
    for owner_id in owner_ids:
        user = await user_repo.get_by_id(owner_id, dynamodb)
        if user:
            owner_map[owner_id] = user.email

    # 6. Build response items with owner info and card_count
    items = []
    for d in page:
        item = _to_dashboard_response(d.model_dump())
        item['my_permission'] = permission_map.get(d.id, "viewer")
        item['card_count'] = len(d.layout) if d.layout else 0
        owner_name = owner_map.get(d.owner_id, "Unknown")
        item['owner'] = {"user_id": d.owner_id or "", "name": owner_name}
        items.append(item)

    return paginated_response(
        items=items,
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
        'id': f"dash_{uuid.uuid4().hex[:12]}",
        'name': dashboard_data.name.strip(),
        'description': dashboard_data.description,
        'layout': dashboard_data.layout,
        'filters': dashboard_data.filters,
        'owner_id': current_user.id,
    }

    # Create dashboard
    repo = DashboardRepository()
    dashboard = await repo.create(create_data, dynamodb)

    return api_response(_to_dashboard_response(dashboard.model_dump()))


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
        HTTPException: 403 if no viewer permission, 404 if not found
    """
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    permission_service = PermissionService()
    await permission_service.assert_permission(
        dashboard, current_user.id, Permission.VIEWER, dynamodb
    )

    return api_response(_to_dashboard_response(dashboard.model_dump()))


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
        HTTPException: 403 if no editor permission, 404 if not found
    """
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    # Check editor permission
    permission_service = PermissionService()
    await permission_service.assert_permission(
        dashboard, current_user.id, Permission.EDITOR, dynamodb
    )

    # Update dashboard
    update_dict = update_data.model_dump(exclude_unset=True)

    updated_dashboard = await repo.update(dashboard_id, update_dict, dynamodb)

    if not updated_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found after update",
        )

    return api_response(_to_dashboard_response(updated_dashboard.model_dump()))


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

    # Check owner permission
    permission_service = PermissionService()
    await permission_service.assert_permission(
        dashboard, current_user.id, Permission.OWNER, dynamodb
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
        HTTPException: 403 if no viewer permission, 404 if source dashboard not found
    """
    repo = DashboardRepository()
    source_dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not source_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    # Check viewer permission
    permission_service = PermissionService()
    await permission_service.assert_permission(
        source_dashboard, current_user.id, Permission.VIEWER, dynamodb
    )

    # Create cloned dashboard with new name and owner
    clone_data = {
        'id': f"dash_{uuid.uuid4().hex[:12]}",
        'name': f"{source_dashboard.name} (Copy)",
        'description': source_dashboard.description,
        'layout': source_dashboard.layout,
        'filters': source_dashboard.filters,
        'owner_id': current_user.id,
    }

    cloned_dashboard = await repo.create(clone_data, dynamodb)

    return api_response(_to_dashboard_response(cloned_dashboard.model_dump()))


@router.get("/{dashboard_id}/referenced-datasets")
async def get_referenced_datasets(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Get datasets referenced by dashboard cards.

    Args:
        dashboard_id: Dashboard ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        List of referenced datasets with usage information

    Raises:
        HTTPException: 403 if no viewer permission, 404 if dashboard not found
    """
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    # Check viewer permission
    permission_service = PermissionService()
    await permission_service.assert_permission(
        dashboard, current_user.id, Permission.VIEWER, dynamodb
    )

    # Get referenced datasets via service
    service = DashboardService()
    referenced_datasets = await service.get_referenced_datasets(
        dashboard=dashboard,
        dynamodb=dynamodb
    )

    return api_response(referenced_datasets)
