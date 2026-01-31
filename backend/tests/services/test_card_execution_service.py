"""Tests for card_execution_service module - TDD RED phase."""
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services.card_execution_service import CardCacheService, CardExecutionService, CardExecutionResult


# ============================================================================
# CardCacheService Tests
# ============================================================================


@pytest.fixture
def mock_dynamodb() -> Any:
    """Create mock DynamoDB resource."""
    mock_table = MagicMock()
    mock_dynamodb_resource = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    return mock_dynamodb_resource


@pytest.fixture
def cache_service(mock_dynamodb: Any) -> CardCacheService:
    """Create CardCacheService instance with mock DynamoDB."""
    return CardCacheService(dynamodb=mock_dynamodb, table_name="test_card_cache")


class TestCardCacheService:
    """Test suite for CardCacheService."""

    def test_cache_key_generation_deterministic(self, cache_service: CardCacheService) -> None:
        """Test that cache_key generation is deterministic (same inputs produce same key)."""
        card_id = "card_123"
        filters = {"category": "A", "date": "2026-01-01"}
        dataset_updated_at = "2026-01-31T10:00:00Z"

        key1 = cache_service.generate_cache_key(card_id, filters, dataset_updated_at)
        key2 = cache_service.generate_cache_key(card_id, filters, dataset_updated_at)

        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 16  # SHA256[:16]

    def test_cache_key_changes_with_filters(self, cache_service: CardCacheService) -> None:
        """Test that cache_key changes when filters change."""
        card_id = "card_123"
        dataset_updated_at = "2026-01-31T10:00:00Z"

        filters1 = {"category": "A"}
        filters2 = {"category": "B"}

        key1 = cache_service.generate_cache_key(card_id, filters1, dataset_updated_at)
        key2 = cache_service.generate_cache_key(card_id, filters2, dataset_updated_at)

        assert key1 != key2

    def test_cache_key_changes_with_card_id(self, cache_service: CardCacheService) -> None:
        """Test that cache_key changes when card_id changes."""
        filters = {"category": "A"}
        dataset_updated_at = "2026-01-31T10:00:00Z"

        key1 = cache_service.generate_cache_key("card_1", filters, dataset_updated_at)
        key2 = cache_service.generate_cache_key("card_2", filters, dataset_updated_at)

        assert key1 != key2

    def test_cache_key_changes_with_dataset_updated_at(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that cache_key changes when dataset_updated_at changes."""
        card_id = "card_123"
        filters = {"category": "A"}

        key1 = cache_service.generate_cache_key(card_id, filters, "2026-01-31T10:00:00Z")
        key2 = cache_service.generate_cache_key(card_id, filters, "2026-01-31T11:00:00Z")

        assert key1 != key2

    def test_set_and_get_roundtrip(self, cache_service: CardCacheService) -> None:
        """Test that set/get roundtrip works correctly."""
        cache_key = "test_key_12345"
        html_content = "<div>Test HTML</div>"
        dataset_id = "dataset_123"

        # Mock DynamoDB put_item
        mock_table = cache_service.table
        mock_table.put_item.return_value = {}

        # Mock DynamoDB get_item
        current_time = int(time.time())
        mock_table.get_item.return_value = {
            "Item": {
                "cache_key": cache_key,
                "html": html_content,
                "dataset_id": dataset_id,
                "created_at": current_time,
                "ttl": current_time + 3600,
            }
        }

        # Set cache
        cache_service.set(cache_key, html_content, dataset_id)

        # Get cache
        result = cache_service.get(cache_key)

        assert result is not None
        assert result["html"] == html_content
        assert result["dataset_id"] == dataset_id

    def test_get_returns_none_when_not_found(self, cache_service: CardCacheService) -> None:
        """Test that get returns None when cache_key not found."""
        cache_key = "nonexistent_key"

        # Mock DynamoDB get_item with no item
        mock_table = cache_service.table
        mock_table.get_item.return_value = {}

        result = cache_service.get(cache_key)

        assert result is None

    def test_get_returns_none_when_ttl_expired(self, cache_service: CardCacheService) -> None:
        """Test that get returns None when TTL is expired."""
        cache_key = "expired_key"
        html_content = "<div>Expired</div>"
        dataset_id = "dataset_123"

        # Mock DynamoDB get_item with expired TTL
        current_time = int(time.time())
        expired_ttl = current_time - 100  # Already expired
        mock_table = cache_service.table
        mock_table.get_item.return_value = {
            "Item": {
                "cache_key": cache_key,
                "html": html_content,
                "dataset_id": dataset_id,
                "created_at": expired_ttl - 3600,
                "ttl": expired_ttl,
            }
        }

        result = cache_service.get(cache_key)

        assert result is None

    def test_set_creates_item_with_ttl(self, cache_service: CardCacheService) -> None:
        """Test that set creates item with proper TTL (3600 seconds)."""
        cache_key = "test_key"
        html_content = "<div>Test</div>"
        dataset_id = "dataset_123"

        mock_table = cache_service.table
        mock_table.put_item.return_value = {}

        cache_service.set(cache_key, html_content, dataset_id)

        # Verify put_item was called
        assert mock_table.put_item.called
        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]

        assert item["cache_key"] == cache_key
        assert item["html"] == html_content
        assert item["dataset_id"] == dataset_id
        assert "created_at" in item
        assert "ttl" in item
        # TTL should be created_at + 3600
        assert item["ttl"] == item["created_at"] + 3600

    def test_invalidate_by_dataset(self, cache_service: CardCacheService) -> None:
        """Test that invalidate_by_dataset removes all cache entries for a dataset."""
        dataset_id = "dataset_123"

        # Mock DynamoDB query to return multiple items
        mock_table = cache_service.table
        mock_table.query.return_value = {
            "Items": [
                {"cache_key": "key1", "dataset_id": dataset_id},
                {"cache_key": "key2", "dataset_id": dataset_id},
            ]
        }
        mock_table.delete_item.return_value = {}

        cache_service.invalidate_by_dataset(dataset_id)

        # Verify query was called with correct parameters
        assert mock_table.query.called
        query_kwargs = mock_table.query.call_args[1]
        assert "IndexName" in query_kwargs
        assert query_kwargs["IndexName"] == "dataset_id-index"

        # Verify delete_item was called twice
        assert mock_table.delete_item.call_count == 2

    def test_immutability_get_does_not_affect_original(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that modifying returned dict from get() does not affect cached data."""
        cache_key = "immutable_test"
        html_content = "<div>Original</div>"
        dataset_id = "dataset_123"

        current_time = int(time.time())
        mock_table = cache_service.table
        mock_table.get_item.return_value = {
            "Item": {
                "cache_key": cache_key,
                "html": html_content,
                "dataset_id": dataset_id,
                "created_at": current_time,
                "ttl": current_time + 3600,
            }
        }

        # Get cache first time
        result1 = cache_service.get(cache_key)
        assert result1 is not None

        # Modify the returned dict
        result1["html"] = "<div>Modified</div>"

        # Get cache second time
        result2 = cache_service.get(cache_key)
        assert result2 is not None

        # Original data should be unchanged
        assert result2["html"] == html_content


# ============================================================================
# CardExecutionService Tests
# ============================================================================


@pytest.fixture
def mock_cache_service() -> MagicMock:
    """Create mock CardCacheService."""
    return MagicMock(spec=CardCacheService)


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Create mock S3 client."""
    return MagicMock()


@pytest.fixture
def execution_service(mock_dynamodb: Any) -> CardExecutionService:
    """Create CardExecutionService instance."""
    return CardExecutionService(dynamodb=mock_dynamodb)


class TestCardExecutionService:
    """Test suite for CardExecutionService."""

    @pytest.mark.asyncio
    async def test_execute_cache_hit(
        self,
        execution_service: CardExecutionService,
        mock_cache_service: MagicMock,
    ) -> None:
        """Test execute returns cached result when cache hit."""
        card_id = "card_123"
        filters = {"category": "A"}
        dataset_updated_at = "2026-01-31T10:00:00Z"
        dataset_id = "dataset_123"

        cached_html = "<div>Cached HTML</div>"
        mock_cache_service.get.return_value = {
            "html": cached_html,
            "dataset_id": dataset_id,
        }

        result = await execution_service.execute(
            card_id=card_id,
            filters=filters,
            dataset_updated_at=dataset_updated_at,
            dataset_id=dataset_id,
            use_cache=True,
            cache_service=mock_cache_service,
        )

        assert result.html == cached_html
        assert result.cached is True
        assert result.execution_time_ms >= 0
        mock_cache_service.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_cache_miss_calls_executor(
        self,
        execution_service: CardExecutionService,
        mock_cache_service: MagicMock,
    ) -> None:
        """Test execute calls Executor API when cache miss."""
        card_id = "card_123"
        filters = {"category": "A"}
        dataset_updated_at = "2026-01-31T10:00:00Z"
        dataset_id = "dataset_123"

        # Cache miss
        mock_cache_service.get.return_value = None

        executor_response = {
            "html": "<div>Executed HTML</div>",
            "used_columns": ["col1", "col2"],
            "filter_applicable": True,
        }

        # Mock httpx AsyncClient
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.json.return_value = executor_response
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await execution_service.execute(
                card_id=card_id,
                filters=filters,
                dataset_updated_at=dataset_updated_at,
                dataset_id=dataset_id,
                use_cache=True,
                cache_service=mock_cache_service,
            )

            assert result.html == executor_response["html"]
            assert result.used_columns == executor_response["used_columns"]
            assert result.filter_applicable is True
            assert result.cached is False
            assert result.execution_time_ms >= 0
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_use_cache_false_bypasses_cache(
        self,
        execution_service: CardExecutionService,
        mock_cache_service: MagicMock,
    ) -> None:
        """Test execute bypasses cache when use_cache=False."""
        card_id = "card_123"
        filters = {"category": "A"}
        dataset_updated_at = "2026-01-31T10:00:00Z"
        dataset_id = "dataset_123"

        executor_response = {
            "html": "<div>Fresh HTML</div>",
            "used_columns": ["col1"],
            "filter_applicable": False,
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.json.return_value = executor_response
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await execution_service.execute(
                card_id=card_id,
                filters=filters,
                dataset_updated_at=dataset_updated_at,
                dataset_id=dataset_id,
                use_cache=False,
                cache_service=mock_cache_service,
            )

            assert result.cached is False
            mock_cache_service.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_handles_timeout(
        self,
        execution_service: CardExecutionService,
        mock_cache_service: MagicMock,
    ) -> None:
        """Test execute handles Executor timeout."""
        import httpx

        card_id = "card_123"
        filters = {}
        dataset_updated_at = "2026-01-31T10:00:00Z"
        dataset_id = "dataset_123"

        mock_cache_service.get.return_value = None

        with patch("httpx.AsyncClient") as mock_client_cls, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="Executor failed after"):
                await execution_service.execute(
                    card_id=card_id,
                    filters=filters,
                    dataset_updated_at=dataset_updated_at,
                    dataset_id=dataset_id,
                    use_cache=True,
                    cache_service=mock_cache_service,
                )

    @pytest.mark.asyncio
    async def test_execute_handles_executor_error(
        self,
        execution_service: CardExecutionService,
        mock_cache_service: MagicMock,
    ) -> None:
        """Test execute handles Executor HTTP error."""
        import httpx

        card_id = "card_123"
        filters = {}
        dataset_updated_at = "2026-01-31T10:00:00Z"
        dataset_id = "dataset_123"

        mock_cache_service.get.return_value = None

        with patch("httpx.AsyncClient") as mock_client_cls, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_500_response = MagicMock()
            mock_500_response.status_code = 500
            mock_500_response.text = "Internal Server Error"
            mock_500_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=mock_500_response,
            )

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_500_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="Executor failed"):
                await execution_service.execute(
                    card_id=card_id,
                    filters=filters,
                    dataset_updated_at=dataset_updated_at,
                    dataset_id=dataset_id,
                    use_cache=True,
                    cache_service=mock_cache_service,
                )

    @pytest.mark.asyncio
    async def test_execute_saves_to_cache_after_execution(
        self,
        execution_service: CardExecutionService,
        mock_cache_service: MagicMock,
    ) -> None:
        """Test execute saves result to cache after successful execution."""
        card_id = "card_123"
        filters = {"category": "A"}
        dataset_updated_at = "2026-01-31T10:00:00Z"
        dataset_id = "dataset_123"

        mock_cache_service.get.return_value = None

        executor_response = {
            "html": "<div>New HTML</div>",
            "used_columns": ["col1"],
            "filter_applicable": True,
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.json.return_value = executor_response
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            await execution_service.execute(
                card_id=card_id,
                filters=filters,
                dataset_updated_at=dataset_updated_at,
                dataset_id=dataset_id,
                use_cache=True,
                cache_service=mock_cache_service,
            )

            # Verify cache.set was called
            mock_cache_service.set.assert_called_once()

    def test_card_execution_result_immutability(self) -> None:
        """Test CardExecutionResult is immutable (frozen dataclass)."""
        result = CardExecutionResult(
            html="<div>Test</div>",
            used_columns=["col1"],
            filter_applicable=True,
            cached=False,
            execution_time_ms=100,
        )

        # Attempt to modify should raise error
        with pytest.raises((AttributeError, Exception)):
            result.html = "<div>Modified</div>"  # type: ignore
