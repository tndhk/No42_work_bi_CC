"""Transform API routes."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.api.response import api_response, paginated_response
from app.models.transform import Transform, TransformCreate, TransformUpdate
from app.models.user import User
from app.repositories.transform_execution_repository import TransformExecutionRepository
from app.repositories.transform_repository import TransformRepository
from app.services.audit_service import AuditService
from app.services.transform_execution_service import TransformExecutionService

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================


def _check_owner_permission(transform: Transform, user_id: str) -> None:
    """Verify user owns the transform.

    Args:
        transform: Transform instance
        user_id: Current user ID

    Raises:
        HTTPException: 403 if user is not owner
    """
    if transform.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this transform",
        )


# ============================================================================
# List Transforms
# ============================================================================


@router.get("")
async def list_transforms(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """List all transforms owned by current user.

    Args:
        limit: Maximum number of items to return (1-100, default: 50)
        offset: Number of items to skip (default: 0)
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Paginated list of transforms
    """
    repo = TransformRepository()
    all_transforms = await repo.list_by_owner(current_user.id, dynamodb)

    # Apply pagination
    total = len(all_transforms)
    transforms = all_transforms[offset:offset + limit]

    return paginated_response(
        items=[t.model_dump() for t in transforms],
        total=total,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# Create Transform
# ============================================================================


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_transform(
    transform_data: TransformCreate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Create a new transform.

    Args:
        transform_data: Transform creation data
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Created transform
    """
    repo = TransformRepository()
    transform_dict = transform_data.model_dump()
    transform_dict["owner_id"] = current_user.id

    transform = await repo.create(transform_dict, dynamodb)
    return api_response(transform.model_dump())


# ============================================================================
# Get Transform
# ============================================================================


@router.get("/{transform_id}")
async def get_transform(
    transform_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Get transform details.

    Args:
        transform_id: Transform ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Transform instance

    Raises:
        HTTPException: 404 if transform not found
    """
    repo = TransformRepository()
    transform = await repo.get_by_id(transform_id, dynamodb)

    if not transform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transform not found",
        )

    return api_response(transform.model_dump())


# ============================================================================
# Update Transform
# ============================================================================


@router.put("/{transform_id}")
async def update_transform(
    transform_id: str,
    transform_update: TransformUpdate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Update transform.

    Args:
        transform_id: Transform ID
        transform_update: Update data
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Updated transform

    Raises:
        HTTPException: 403 if not owner, 404 if transform not found
    """
    repo = TransformRepository()
    transform = await repo.get_by_id(transform_id, dynamodb)

    if not transform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transform not found",
        )

    _check_owner_permission(transform, current_user.id)

    # Update transform
    updates = transform_update.model_dump(exclude_unset=True)
    updated_transform = await repo.update(transform_id, updates, dynamodb)

    if not updated_transform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transform not found after update",
        )

    return api_response(updated_transform.model_dump())


# ============================================================================
# Delete Transform
# ============================================================================


@router.delete("/{transform_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transform(
    transform_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> None:
    """Delete transform.

    Args:
        transform_id: Transform ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Raises:
        HTTPException: 403 if not owner, 404 if transform not found
    """
    repo = TransformRepository()
    transform = await repo.get_by_id(transform_id, dynamodb)

    if not transform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transform not found",
        )

    _check_owner_permission(transform, current_user.id)

    await repo.delete(transform_id, dynamodb)


# ============================================================================
# Execute Transform
# ============================================================================


@router.post("/{transform_id}/execute")
async def execute_transform(
    transform_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
    s3: Any = Depends(get_s3_client),
) -> dict[str, Any]:
    """Execute transform and create output dataset.

    This endpoint runs the transform's code against its input datasets,
    creates a new output dataset, and updates the transform's output_dataset_id.

    Args:
        transform_id: Transform ID to execute
        current_user: Authenticated user (must be owner)
        dynamodb: DynamoDB resource
        s3: S3 client

    Returns:
        Execution result including output_dataset_id, row_count, columns, time

    Raises:
        HTTPException: 403 if not owner, 404 if transform not found,
                      400 if input dataset not found, 500 if executor fails
    """
    repo = TransformRepository()
    transform = await repo.get_by_id(transform_id, dynamodb)

    if not transform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transform not found",
        )

    _check_owner_permission(transform, current_user.id)

    # Execute transform
    service = TransformExecutionService()
    try:
        result = await service.execute(
            transform=transform,
            dynamodb=dynamodb,
            s3=s3,
        )
    except ValueError as e:
        # Input dataset not found or has no data
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        # Executor failed
        await AuditService().log_transform_failed(
            user_id=current_user.id,
            transform_id=transform_id,
            error=str(e),
            dynamodb=dynamodb,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    await AuditService().log_transform_executed(
        user_id=current_user.id,
        transform_id=transform_id,
        execution_id=result.execution_id,
        dynamodb=dynamodb,
    )

    return api_response({
        "execution_id": result.execution_id,
        "output_dataset_id": result.output_dataset_id,
        "row_count": result.row_count,
        "column_names": result.column_names,
        "execution_time_ms": result.execution_time_ms,
    })


# ============================================================================
# List Transform Executions
# ============================================================================


@router.get("/{transform_id}/executions")
async def list_transform_executions(
    transform_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """List execution history for a transform.

    Args:
        transform_id: Transform ID
        limit: Maximum number of items to return (1-100, default: 20)
        offset: Number of items to skip (default: 0)
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Paginated list of transform executions

    Raises:
        HTTPException: 404 if transform not found
    """
    # Verify transform exists
    repo = TransformRepository()
    transform = await repo.get_by_id(transform_id, dynamodb)
    if not transform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transform not found",
        )

    # Get executions
    exec_repo = TransformExecutionRepository()
    all_executions = await exec_repo.list_by_transform(
        transform_id, dynamodb, limit=limit + offset,
    )
    total = len(all_executions)
    executions = all_executions[offset:offset + limit]

    return paginated_response(
        items=[e.model_dump() for e in executions],
        total=total,
        limit=limit,
        offset=offset,
    )
