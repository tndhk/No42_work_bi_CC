"""Card API routes."""
import uuid
from typing import Any, Optional
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
    code: Optional[str] = None  # Optional: フロントからのコード（未保存のコードをプレビューするため）
    dataset_id: Optional[str] = None  # Optional: 新規カード用


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


async def _enrich_card_with_dataset(
    card_dict: dict[str, Any],
    dataset_id: str | None,
    dynamodb: Any,
) -> dict[str, Any]:
    """Enrich card dict with dataset info if dataset_id is present.

    Args:
        card_dict: Card data as dictionary
        dataset_id: Dataset ID (may be None)
        dynamodb: DynamoDB resource

    Returns:
        Enriched card dict with dataset info added if available
    """
    if dataset_id:
        dataset_repo = DatasetRepository()
        dataset = await dataset_repo.get_by_id(dataset_id, dynamodb)
        if dataset:
            card_dict["dataset"] = {"id": dataset.id, "name": dataset.name}
    return card_dict


async def _get_card_and_dataset(
    card_id: str,
    dynamodb: Any,
) -> tuple[Card, Dataset | None]:
    """Get card and its associated dataset.

    Args:
        card_id: Card ID
        dynamodb: DynamoDB resource

    Returns:
        Tuple of (Card, Dataset | None). Dataset is None for text cards.

    Raises:
        HTTPException: 404 if card not found, 422 if code card has no dataset_id,
                       404 if dataset not found
    """
    card_repo = CardRepository()
    card = await card_repo.get_by_id(card_id, dynamodb)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    # Text cards don't require dataset
    if card.card_type == "text":
        return card, None

    # Code cards require dataset
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
    dataset: Dataset | None,
    filters: dict[str, Any],
    use_cache: bool,
    current_user: User,
    card_id: str,
    dynamodb: Any,
    override_code: str | None = None,
    override_dataset_id: str | None = None,
) -> dict[str, Any]:
    """Execute card with error handling and audit logging.

    Args:
        execution_service: Card execution service
        cache_service: Cache service
        card: Card instance
        dataset: Dataset instance (None for text cards)
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
        # Use override code if provided, otherwise use card.code
        code_to_execute = override_code if override_code is not None else card.code
        dataset_id_to_use = override_dataset_id if override_dataset_id is not None else card.dataset_id

        # Text cards don't need executor - return code as HTML directly
        card_type = card.card_type if card else "code"
        if card_type == "text":
            import time
            start_time = time.perf_counter()
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return api_response({
                "html": code_to_execute,
                "used_columns": [],
                "filter_applicable": False,
                "cached": False,
                "execution_time_ms": elapsed_ms,
            })

        # Code cards require dataset
        if not dataset and not override_dataset_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Card has no dataset_id",
            )

        # Use override dataset_id if provided, otherwise use dataset from card
        final_dataset_id = override_dataset_id if override_dataset_id else (dataset.id if dataset else None)
        if not final_dataset_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Dataset ID is required",
            )

        # Get dataset for updated_at if we have a dataset object, otherwise fetch it
        if dataset:
            dataset_updated_at = dataset.updated_at.isoformat()
        else:
            dataset_repo = DatasetRepository()
            dataset_obj = await dataset_repo.get_by_id(final_dataset_id, dynamodb)
            if not dataset_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            dataset_updated_at = dataset_obj.updated_at.isoformat()

        result = await execution_service.execute(
            card_id=card_id,
            filters=filters,
            dataset_updated_at=dataset_updated_at,
            dataset_id=final_dataset_id,
            use_cache=use_cache,
            cache_service=cache_service,
            code=code_to_execute,
            params=card.params if card else None,
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
    all_cards = await repo.list_by_owner(current_user.id, dynamodb)

    # Apply pagination
    total = len(all_cards)
    cards = all_cards[offset:offset + limit]

    # Enrich cards with dataset and owner info
    enriched_cards = []
    for card in cards:
        card_dict = card.model_dump()
        # Add dataset info
        card_dict = await _enrich_card_with_dataset(
            card_dict, card.dataset_id, dynamodb
        )
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

    # Enrich with dataset info for frontend compatibility
    result_dict = card.model_dump()
    result_dict = await _enrich_card_with_dataset(
        result_dict, card.dataset_id, dynamodb
    )

    return api_response(result_dict)


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
    card_dict = await _enrich_card_with_dataset(
        card_dict, card.dataset_id, dynamodb
    )

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

    # Enrich with dataset info for frontend compatibility
    card_dict = updated_card.model_dump()
    card_dict = await _enrich_card_with_dataset(
        card_dict, updated_card.dataset_id, dynamodb
    )

    return api_response(card_dict)


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


@router.post("/preview")
async def preview_draft_card(
    preview_req: PreviewRequest,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
    s3_client: Any = Depends(get_s3_client),
) -> dict[str, Any]:
    """Preview card execution with code and dataset_id (no cache, for draft cards).

    Args:
        preview_req: Preview request with code, dataset_id, and filters
        current_user: Authenticated user
        dynamodb: DynamoDB resource
        s3_client: S3 client for dataset access

    Returns:
        Execution result

    Raises:
        HTTPException: 422 if code or dataset_id missing, 404 if dataset not found, 500 if execution fails
    """
    if not preview_req.code:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="code is required",
        )

    if not preview_req.dataset_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="dataset_id is required",
        )

    # Create a minimal Card-like object for execution
    from app.models.card import Card
    from datetime import datetime
    draft_card = Card(
        id="draft",
        name="Draft",
        code=preview_req.code,
        card_type="code",
        dataset_id=preview_req.dataset_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    execution_service, cache_service = _create_execution_services(dynamodb, s3_client)

    return await _execute_card_with_error_handling(
        execution_service=execution_service,
        cache_service=cache_service,
        card=draft_card,
        dataset=None,
        filters=preview_req.filters,
        use_cache=False,
        current_user=current_user,
        card_id="draft",
        dynamodb=dynamodb,
        override_code=preview_req.code,
        override_dataset_id=preview_req.dataset_id,
    )


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
        preview_req: Preview request with filters (optionally code and dataset_id)
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
        override_code=preview_req.code,
        override_dataset_id=preview_req.dataset_id,
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


# ============================================================================
# Get Card Data
# ============================================================================


@router.get("/{card_id}/data")
async def get_card_data(
    card_id: str,
    limit: int = Query(1000, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
    s3_client: Any = Depends(get_s3_client),
) -> dict[str, Any]:
    """Get card's underlying dataset data.

    Args:
        card_id: Card ID
        limit: Maximum number of rows to return (1-1000, default: 1000)
        current_user: Authenticated user
        dynamodb: DynamoDB resource
        s3_client: S3 client for dataset access

    Returns:
        Dataset data with columns and rows

    Raises:
        HTTPException: 404 if card not found or dataset not found
    """
    card, dataset = await _get_card_and_dataset(card_id, dynamodb)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    # Read dataset rows from S3
    from app.services.parquet_storage import ParquetReader
    from app.core.config import settings

    reader = ParquetReader(s3_client, settings.s3_bucket_datasets)

    try:
        df = await reader.read_preview(dataset.s3_path, limit)
    except DatasetFileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file not found: {e.s3_path}",
        ) from e

    # Get total row count (approximate for partitioned datasets)
    try:
        df_full = await reader.read_full(dataset.s3_path)
        total_rows = len(df_full)
    except Exception:
        # If we can't read full dataset, use preview count
        total_rows = len(df)

    # Convert DataFrame to list of dicts
    rows = df.to_dict(orient='records')
    columns = df.columns.tolist()

    return api_response({
        "columns": columns,
        "rows": rows,
        "total_rows": total_rows,
        "returned_rows": len(rows),
        "truncated": total_rows > len(rows),
    })
