"""Card API routes."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user, get_dynamodb_resource
from app.models.card import Card, CardCreate, CardUpdate
from app.models.user import User
from app.repositories.card_repository import CardRepository
from app.repositories.dataset_repository import DatasetRepository
from app.services.card_execution_service import (
    CardCacheService,
    CardExecutionService,
)
from app.core.config import settings

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


# ============================================================================
# List Cards
# ============================================================================


@router.get("", response_model=list[Card])
async def list_cards(
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> list[Card]:
    """List all cards owned by current user.

    Args:
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        List of cards
    """
    repo = CardRepository()
    cards = await repo.list_by_owner(current_user.id, dynamodb)
    return cards


# ============================================================================
# Create Card
# ============================================================================


@router.post("", response_model=Card, status_code=status.HTTP_201_CREATED)
async def create_card(
    card_data: CardCreate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> Card:
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
    card_dict["owner_id"] = current_user.id

    card = await repo.create(card_dict, dynamodb)
    return card


# ============================================================================
# Get Card
# ============================================================================


@router.get("/{card_id}", response_model=Card)
async def get_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> Card:
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

    return card


# ============================================================================
# Update Card
# ============================================================================


@router.put("/{card_id}", response_model=Card)
async def update_card(
    card_id: str,
    card_update: CardUpdate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> Card:
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

    return updated_card


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


@router.post("/{card_id}/preview", response_model=ExecutionResponse)
async def preview_card(
    card_id: str,
    preview_req: PreviewRequest,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> ExecutionResponse:
    """Preview card execution with filters (no cache).

    Args:
        card_id: Card ID
        preview_req: Preview request with filters
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Execution result

    Raises:
        HTTPException: 404 if card not found, 500 if execution fails
    """
    # Get card
    card_repo = CardRepository()
    card = await card_repo.get_by_id(card_id, dynamodb)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    # Get dataset for updated_at
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

    # Execute without cache
    execution_service = CardExecutionService(dynamodb=dynamodb)
    cache_service = CardCacheService(
        dynamodb=dynamodb,
        table_name=f"{settings.dynamodb_table_prefix}card_cache",
    )

    try:
        result = await execution_service.execute(
            card_id=card.id,
            filters=preview_req.filters,
            dataset_updated_at=dataset.updated_at.isoformat(),
            dataset_id=card.dataset_id,
            use_cache=False,
            cache_service=cache_service,
        )

        return ExecutionResponse(
            html=result.html,
            used_columns=result.used_columns,
            filter_applicable=result.filter_applicable,
            cached=result.cached,
            execution_time_ms=result.execution_time_ms,
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================================
# Execute Card
# ============================================================================


@router.post("/{card_id}/execute", response_model=ExecutionResponse)
async def execute_card(
    card_id: str,
    execute_req: ExecuteRequest,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> ExecutionResponse:
    """Execute card with optional caching.

    Args:
        card_id: Card ID
        execute_req: Execute request with filters and cache setting
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Execution result

    Raises:
        HTTPException: 404 if card not found, 500 if execution fails
    """
    # Get card
    card_repo = CardRepository()
    card = await card_repo.get_by_id(card_id, dynamodb)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    # Get dataset for updated_at
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

    # Execute with cache
    execution_service = CardExecutionService(dynamodb=dynamodb)
    cache_service = CardCacheService(
        dynamodb=dynamodb,
        table_name=f"{settings.dynamodb_table_prefix}card_cache",
    )

    try:
        result = await execution_service.execute(
            card_id=card.id,
            filters=execute_req.filters,
            dataset_updated_at=dataset.updated_at.isoformat(),
            dataset_id=card.dataset_id,
            use_cache=execute_req.use_cache,
            cache_service=cache_service,
        )

        return ExecutionResponse(
            html=result.html,
            used_columns=result.used_columns,
            filter_applicable=result.filter_applicable,
            cached=result.cached,
            execution_time_ms=result.execution_time_ms,
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
