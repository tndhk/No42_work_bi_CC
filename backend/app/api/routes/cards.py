"""Card API routes."""
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.api.response import api_response, paginated_response
from app.models.card import Card, CardCreate, CardUpdate
from app.models.dataset import Dataset
from app.models.user import User
from app.repositories.card_repository import CardRepository
from app.repositories.dataset_repository import DatasetRepository
from app.services.card_execution_service import (
    CardCacheService,
    CardExecutionService,
)
from app.core.config import settings
from app.services.audit_service import AuditService
from app.exceptions import DatasetFileNotFoundError

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class PreviewRequest(BaseModel):
    """Preview request model."""

    filters: dict[str, Any] = {}


class ExecuteRequest(BaseModel):
    """Execute request model."""

    filters: dict[str, Any] = {}
    use_cache: bool = True


class ExecutionResponse(BaseModel):
    """Execution response model."""

    html: str
    used_columns: list[str]
    filter_applicable: bool
    cached: bool
    execution_time_ms: int


# ============================================================================
# Helper Functions
# ============================================================================


def _check_owner_permission(card: Card, user_id: str) -> None:
    """Verify user owns the card.

    Args:
        card: Card instance
        user_id: Current user ID

    Raises:
        HTTPException: 403 if user is not owner
    """
    if card.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this card",
        )


async def _get_card_and_dataset(
    card_id: str,
    dynamodb: Any,
) -> tuple[Card, Dataset]:
    """Get card and its associated dataset.

    Args:
        card_id: Card ID
        dynamodb: DynamoDB resource

    Returns:
        Tuple of (Card, Dataset)

    Raises:
        HTTPException: 404 if card not found, 422 if card has no dataset_id,
                       404 if dataset not found
    """
    card_repo = CardRepository()
    card = await card_repo.get_by_id(card_id, dynamodb)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    if not card.dataset_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Card has no dataset_id",
        )

    dataset_repo = DatasetRepository()
    dataset = await dataset_repo.get_by_id(card.dataset_id, dynamodb)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return card, dataset


def _create_execution_services(
    dynamodb: Any,
    s3_client: Any,
) -> tuple[CardExecutionService, CardCacheService]:
    """Create card execution and cache services.

    Args:
        dynamodb: DynamoDB resource
        s3_client: S3 client

    Returns:
        Tuple of (CardExecutionService, CardCacheService)
    """
    execution_service = CardExecutionService(dynamodb=dynamodb, s3_client=s3_client)
    cache_service = CardCacheService(
        dynamodb=dynamodb,
        table_name=f"{settings.dynamodb_table_prefix}card_cache",
    )
    return execution_service, cache_service


async def _execute_card_with_error_handling(
    execution_service: CardExecutionService,
    cache_service: CardCacheService,
    card: Card,
    dataset: Dataset,
    filters: dict[str, Any],
    use_cache: bool,
    current_user: User,
    card_id: str,
    dynamodb: Any,
) -> dict[str, Any]:
    """Execute card with error handling and audit logging.

    Args:
        execution_service: Card execution service
        cache_service: Cache service
        card: Card instance
        dataset: Dataset instance
        filters: Filter parameters
        use_cache: Whether to use cache
        current_user: Current user
        card_id: Card ID
        dynamodb: DynamoDB resource

    Returns:
        API response with execution result

    Raises:
        HTTPException: 500 if execution fails
    """
    try:
        result = await execution_service.execute(
            card_id=card.id,
            filters=filters,
            dataset_updated_at=dataset.updated_at.isoformat(),
            dataset_id=card.dataset_id,
            use_cache=use_cache,
            cache_service=cache_service,
            code=card.code,
        )

        return api_response({
            "html": result.html,
            "used_columns": result.used_columns,
            "filter_applicable": result.filter_applicable,
            "cached": result.cached,
            "execution_time_ms": result.execution_time_ms,
        })

    except (DatasetFileNotFoundError, RuntimeError) as e:
        await AuditService().log_card_execution_failed(
            user_id=current_user.id,
            card_id=card_id,
            error=str(e),
            dynamodb=dynamodb,
        )
        if isinstance(e, DatasetFileNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
            detail = (
                f"Dataset file not found (dataset_id: {e.dataset_id})"
                if e.dataset_id is not None
                else "Dataset file not found"
            )
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            detail = str(e)
        raise HTTPException(status_code=status_code, detail=detail)


# ============================================================================
# List Cards
# ============================================================================


@router.get("")
async def list_cards(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """List all cards owned by current user.

    Args:
        limit: Maximum number of items to return (1-100, default: 50)
        offset: Number of items to skip (default: 0)
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Paginated list of cards
    """
    repo = CardRepository()
    dataset_repo = DatasetRepository()
    all_cards = await repo.list_by_owner(current_user.id, dynamodb)

    # Apply pagination
    total = len(all_cards)
    cards = all_cards[offset:offset + limit]

    # Enrich cards with dataset and owner info
    enriched_cards = []
    for card in cards:
        card_dict = card.model_dump()
        # Add dataset info
        if card.dataset_id:
            dataset = await dataset_repo.get_by_id(card.dataset_id, dynamodb)
            if dataset:
                card_dict["dataset"] = {"id": dataset.id, "name": dataset.name}
        # Add owner info (current user owns all listed cards)
        card_dict["owner"] = {"user_id": current_user.id, "name": current_user.email}
        enriched_cards.append(card_dict)

    return paginated_response(
        items=enriched_cards,
        total=total,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# Create Card
# ============================================================================


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_card(
    card_data: CardCreate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Create a new card.

    Args:
        card_data: Card creation data
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Created card

    Raises:
        HTTPException: 404 if dataset not found, 422 if validation fails
    """
    # Verify dataset exists if provided
    if card_data.dataset_id:
        dataset_repo = DatasetRepository()
        dataset = await dataset_repo.get_by_id(card_data.dataset_id, dynamodb)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

    # Create card
    repo = CardRepository()
    card_dict = card_data.model_dump()
    card_dict["id"] = f"card_{uuid.uuid4().hex[:12]}"
    card_dict["owner_id"] = current_user.id

    card = await repo.create(card_dict, dynamodb)
    return api_response(card.model_dump())


# ============================================================================
# Get Card
# ============================================================================


@router.get("/{card_id}")
async def get_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Get card details.

    Args:
        card_id: Card ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Card instance

    Raises:
        HTTPException: 404 if card not found
    """
    repo = CardRepository()
    card = await repo.get_by_id(card_id, dynamodb)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    # Enrich with dataset info for frontend compatibility
    card_dict = card.model_dump()
    if card.dataset_id:
        dataset_repo = DatasetRepository()
        dataset = await dataset_repo.get_by_id(card.dataset_id, dynamodb)
        if dataset:
            card_dict["dataset"] = {"id": dataset.id, "name": dataset.name}

    return api_response(card_dict)


# ============================================================================
# Update Card
# ============================================================================


@router.put("/{card_id}")
async def update_card(
    card_id: str,
    card_update: CardUpdate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """Update card.

    Args:
        card_id: Card ID
        card_update: Update data
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Updated card

    Raises:
        HTTPException: 403 if not owner, 404 if card not found
    """
    repo = CardRepository()
    card = await repo.get_by_id(card_id, dynamodb)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    _check_owner_permission(card, current_user.id)

    # Update card
    updates = card_update.model_dump(exclude_unset=True)
    updated_card = await repo.update(card_id, updates, dynamodb)

    if not updated_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found after update",
        )

    return api_response(updated_card.model_dump())


# ============================================================================
# Delete Card
# ============================================================================


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> None:
    """Delete card.

    Args:
        card_id: Card ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Raises:
        HTTPException: 403 if not owner, 404 if card not found
    """
    repo = CardRepository()
    card = await repo.get_by_id(card_id, dynamodb)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    _check_owner_permission(card, current_user.id)

    await repo.delete(card_id, dynamodb)


# ============================================================================
# Preview Card
# ============================================================================


@router.post("/{card_id}/preview")
async def preview_card(
    card_id: str,
    preview_req: PreviewRequest,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
    s3_client: Any = Depends(get_s3_client),
) -> dict[str, Any]:
    """Preview card execution with filters (no cache).

    Args:
        card_id: Card ID
        preview_req: Preview request with filters
        current_user: Authenticated user
        dynamodb: DynamoDB resource
        s3_client: S3 client for dataset access

    Returns:
        Execution result

    Raises:
        HTTPException: 404 if card not found, 500 if execution fails
    """
    card, dataset = await _get_card_and_dataset(card_id, dynamodb)
    execution_service, cache_service = _create_execution_services(dynamodb, s3_client)

    return await _execute_card_with_error_handling(
        execution_service=execution_service,
        cache_service=cache_service,
        card=card,
        dataset=dataset,
        filters=preview_req.filters,
        use_cache=False,
        current_user=current_user,
        card_id=card_id,
        dynamodb=dynamodb,
    )


# ============================================================================
# Execute Card
# ============================================================================


@router.post("/{card_id}/execute")
async def execute_card(
    card_id: str,
    execute_req: ExecuteRequest,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
    s3_client: Any = Depends(get_s3_client),
) -> dict[str, Any]:
    """Execute card with optional caching.

    Args:
        card_id: Card ID
        execute_req: Execute request with filters and cache setting
        current_user: Authenticated user
        dynamodb: DynamoDB resource
        s3_client: S3 client for dataset access

    Returns:
        Execution result

    Raises:
        HTTPException: 404 if card not found, 500 if execution fails
    """
    card, dataset = await _get_card_and_dataset(card_id, dynamodb)
    execution_service, cache_service = _create_execution_services(dynamodb, s3_client)

    return await _execute_card_with_error_handling(
        execution_service=execution_service,
        cache_service=cache_service,
        card=card,
        dataset=dataset,
        filters=execute_req.filters,
        use_cache=execute_req.use_cache,
        current_user=current_user,
        card_id=card_id,
        dynamodb=dynamodb,
    )
