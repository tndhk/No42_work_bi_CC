"""Card execution and caching services."""
import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5  # seconds


class CardCacheService:
    """Service for caching card execution results in DynamoDB."""

    def __init__(self, dynamodb: Any, table_name: str) -> None:
        """Initialize CardCacheService.

        Args:
            dynamodb: DynamoDB resource instance
            table_name: Name of the DynamoDB cache table
        """
        self.dynamodb = dynamodb
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)

    def generate_cache_key(
        self,
        card_id: str,
        filters: dict[str, Any],
        dataset_updated_at: str,
    ) -> str:
        """Generate deterministic cache key.

        Args:
            card_id: Card identifier
            filters: Filter parameters
            dataset_updated_at: Dataset last update timestamp

        Returns:
            16-character cache key (SHA256 hash prefix)
        """
        filters_json = json.dumps(filters, sort_keys=True)
        combined = f"{card_id}:{filters_json}:{dataset_updated_at}"
        hash_digest = hashlib.sha256(combined.encode()).hexdigest()
        return hash_digest[:16]

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """Retrieve cached HTML from DynamoDB.

        Args:
            cache_key: Cache key to retrieve

        Returns:
            Dict with html and metadata if found and not expired, None otherwise
        """
        try:
            response = self.table.get_item(Key={"cache_key": cache_key})
            item = response.get("Item")

            if not item:
                return None

            # Check TTL expiration
            current_time = int(time.time())
            if item["ttl"] <= current_time:
                return None

            # Return immutable copy
            return {
                "html": item["html"],
                "dataset_id": item["dataset_id"],
                "created_at": item["created_at"],
                "ttl": item["ttl"],
                "cache_key": item["cache_key"],
            }

        except ClientError:
            return None

    def set(self, cache_key: str, html: str, dataset_id: str) -> None:
        """Store HTML in cache with TTL.

        Args:
            cache_key: Cache key
            html: HTML content to cache
            dataset_id: Associated dataset ID for invalidation
        """
        current_time = int(time.time())
        ttl = current_time + settings.cache_ttl_seconds

        item = {
            "cache_key": cache_key,
            "html": html,
            "dataset_id": dataset_id,
            "created_at": current_time,
            "ttl": ttl,
        }

        try:
            self.table.put_item(Item=item)
        except ClientError as e:
            raise RuntimeError(f"Failed to cache item: {e}") from e

    def invalidate_by_dataset(self, dataset_id: str) -> None:
        """Invalidate all cache entries for a dataset.

        Args:
            dataset_id: Dataset ID to invalidate
        """
        try:
            response = self.table.query(
                IndexName="dataset_id-index",
                KeyConditionExpression="dataset_id = :dataset_id",
                ExpressionAttributeValues={":dataset_id": dataset_id},
            )

            items = response.get("Items", [])
            for item in items:
                self.table.delete_item(Key={"cache_key": item["cache_key"]})

        except ClientError as e:
            raise RuntimeError(f"Failed to invalidate cache: {e}") from e


@dataclass(frozen=True)
class CardExecutionResult:
    """Immutable result from card execution."""

    html: str
    used_columns: list[str]
    filter_applicable: bool
    cached: bool
    execution_time_ms: int


class CardExecutionService:
    """Service for executing cards via Executor API."""

    def __init__(self, dynamodb: Any) -> None:
        """Initialize CardExecutionService.

        Args:
            dynamodb: DynamoDB resource instance
        """
        self.dynamodb = dynamodb

    async def execute(
        self,
        card_id: str,
        filters: dict[str, Any],
        dataset_updated_at: str,
        dataset_id: str,
        use_cache: bool,
        cache_service: CardCacheService,
        code: str = "",
    ) -> CardExecutionResult:
        """Execute card with optional caching.

        Args:
            card_id: Card identifier
            filters: Filter parameters
            dataset_updated_at: Dataset last update timestamp
            dataset_id: Dataset identifier
            use_cache: Whether to use cache
            cache_service: Cache service instance
            code: Python code for the card's render function

        Returns:
            CardExecutionResult with execution details

        Raises:
            RuntimeError: If executor fails or times out after retries
        """
        start_time = time.perf_counter()

        # Try cache if enabled
        if use_cache:
            cache_key = cache_service.generate_cache_key(
                card_id, filters, dataset_updated_at
            )
            cached = cache_service.get(cache_key)
            if cached:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                return CardExecutionResult(
                    html=cached["html"],
                    used_columns=[],
                    filter_applicable=False,
                    cached=True,
                    execution_time_ms=elapsed_ms,
                )

        # Execute via Executor API with retry
        data = await self._execute_with_retry(
            card_id=card_id,
            code=code,
            filters=filters,
            dataset_id=dataset_id,
        )

        # Save to cache if enabled
        if use_cache:
            cache_service.set(cache_key, data["html"], dataset_id)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return CardExecutionResult(
            html=data["html"],
            used_columns=data.get("used_columns", []),
            filter_applicable=data.get("filter_applicable", False),
            cached=False,
            execution_time_ms=elapsed_ms,
        )

    async def _execute_with_retry(
        self,
        card_id: str,
        code: str,
        filters: dict[str, Any],
        dataset_id: str,
    ) -> dict[str, Any]:
        """Execute card via Executor API with exponential backoff retry.

        Retries up to MAX_RETRIES times on transient errors (connection errors,
        5xx status codes). Non-retryable errors (4xx) are raised immediately.

        Args:
            card_id: Card identifier
            code: Python code for the card
            filters: Filter parameters
            dataset_id: Dataset identifier

        Returns:
            Response data dict from executor

        Raises:
            RuntimeError: If all retries are exhausted
        """
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(
                    timeout=settings.executor_timeout_seconds
                ) as client:
                    response = await client.post(
                        f"{settings.executor_url}/execute/card",
                        json={
                            "card_id": card_id,
                            "code": code,
                            "filters": filters,
                            "dataset_id": dataset_id,
                        },
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise RuntimeError(
                        f"Executor returned client error: {e.response.status_code} - {e.response.text}"
                    ) from e
                last_error = e
                logger.warning(
                    "Executor request failed (attempt %d/%d): %s",
                    attempt + 1, MAX_RETRIES, e,
                )

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                logger.warning(
                    "Executor request failed (attempt %d/%d): %s",
                    attempt + 1, MAX_RETRIES, e,
                )

            # Exponential backoff
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"Executor failed after {MAX_RETRIES} attempts: {last_error}"
        )
