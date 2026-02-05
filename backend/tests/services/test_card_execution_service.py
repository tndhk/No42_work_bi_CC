"""Tests for card_execution_service module - TDD RED phase."""
import time
from typing import Any
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

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
        # Given: Same card_id, filters, and dataset_updated_at
        card_id = "card_123"
        filters = {"category": "A", "date": "2026-01-01"}
        dataset_updated_at = "2026-01-31T10:00:00Z"

        # When: Generating cache key twice with same inputs
        key1 = cache_service.generate_cache_key(card_id, filters, dataset_updated_at)
        key2 = cache_service.generate_cache_key(card_id, filters, dataset_updated_at)

        # Then: Both keys should be identical and have correct format
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 16  # SHA256[:16]

    def test_cache_key_changes_with_filters(self, cache_service: CardCacheService) -> None:
        """Test that cache_key changes when filters change."""
        # Given: Same card_id and dataset_updated_at, but different filters
        card_id = "card_123"
        dataset_updated_at = "2026-01-31T10:00:00Z"

        filters1 = {"category": "A"}
        filters2 = {"category": "B"}

        # When: Generating cache keys with different filters
        key1 = cache_service.generate_cache_key(card_id, filters1, dataset_updated_at)
        key2 = cache_service.generate_cache_key(card_id, filters2, dataset_updated_at)

        # Then: Keys should be different
        assert key1 != key2

    def test_cache_key_changes_with_card_id(self, cache_service: CardCacheService) -> None:
        """Test that cache_key changes when card_id changes."""
        # Given: Same filters and dataset_updated_at, but different card_id
        filters = {"category": "A"}
        dataset_updated_at = "2026-01-31T10:00:00Z"

        # When: Generating cache keys with different card_ids
        key1 = cache_service.generate_cache_key("card_1", filters, dataset_updated_at)
        key2 = cache_service.generate_cache_key("card_2", filters, dataset_updated_at)

        # Then: Keys should be different
        assert key1 != key2

    def test_cache_key_changes_with_dataset_updated_at(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that cache_key changes when dataset_updated_at changes."""
        # Given: Same card_id and filters, but different dataset_updated_at
        card_id = "card_123"
        filters = {"category": "A"}

        # When: Generating cache keys with different dataset_updated_at values
        key1 = cache_service.generate_cache_key(card_id, filters, "2026-01-31T10:00:00Z")
        key2 = cache_service.generate_cache_key(card_id, filters, "2026-01-31T11:00:00Z")

        # Then: Keys should be different
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_set_and_get_roundtrip(self, cache_service: CardCacheService) -> None:
        """Test that set/get roundtrip works correctly."""
        # Given: Valid cache key, HTML content, and dataset ID with mocked DynamoDB
        cache_key = "test_key_12345"
        html_content = "<div>Test HTML</div>"
        dataset_id = "dataset_123"

        # Mock DynamoDB put_item
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # Mock DynamoDB get_item
        current_time = int(time.time())
        mock_table.get_item = AsyncMock(return_value={
            "Item": {
                "cache_key": cache_key,
                "html": html_content,
                "dataset_id": dataset_id,
                "created_at": current_time,
                "ttl": current_time + 3600,
            }
        })

        # When: Setting cache and then getting it
        await cache_service.set(cache_key, html_content, dataset_id)
        result = await cache_service.get(cache_key)

        # Then: Result should contain the original HTML and dataset_id
        assert result is not None
        assert result["html"] == html_content
        assert result["dataset_id"] == dataset_id

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self, cache_service: CardCacheService) -> None:
        """Test that get returns None when cache_key not found."""
        # Given: Non-existent cache key and DynamoDB returning no item
        cache_key = "nonexistent_key"

        # Mock DynamoDB get_item with no item
        mock_table = AsyncMock()
        mock_table.get_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Getting cache with non-existent key
        result = await cache_service.get(cache_key)

        # Then: Result should be None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_when_ttl_expired(self, cache_service: CardCacheService) -> None:
        """Test that get returns None when TTL is expired."""
        # Given: Cache item with expired TTL
        cache_key = "expired_key"
        html_content = "<div>Expired</div>"
        dataset_id = "dataset_123"

        # Mock DynamoDB get_item with expired TTL
        current_time = int(time.time())
        expired_ttl = current_time - 100  # Already expired
        mock_table = AsyncMock()
        mock_table.get_item = AsyncMock(return_value={
            "Item": {
                "cache_key": cache_key,
                "html": html_content,
                "dataset_id": dataset_id,
                "created_at": expired_ttl - 3600,
                "ttl": expired_ttl,
            }
        })
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Getting cache with expired TTL
        result = await cache_service.get(cache_key)

        # Then: Result should be None
        assert result is None

    @pytest.mark.asyncio
    async def test_set_creates_item_with_ttl(self, cache_service: CardCacheService) -> None:
        """Test that set creates item with proper TTL (3600 seconds)."""
        # Given: Valid cache key, HTML content, dataset ID, and mocked DynamoDB
        cache_key = "test_key"
        html_content = "<div>Test</div>"
        dataset_id = "dataset_123"

        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Setting cache
        await cache_service.set(cache_key, html_content, dataset_id)

        # Then: put_item should be called with correct item structure and TTL
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

    @pytest.mark.asyncio
    async def test_invalidate_by_dataset(self, cache_service: CardCacheService) -> None:
        """Test that invalidate_by_dataset removes all cache entries for a dataset."""
        # Given: Dataset ID and DynamoDB query returning multiple cache entries
        dataset_id = "dataset_123"

        # Mock DynamoDB query to return multiple items
        mock_table = AsyncMock()
        mock_table.query = AsyncMock(return_value={
            "Items": [
                {"cache_key": "key1", "dataset_id": dataset_id},
                {"cache_key": "key2", "dataset_id": dataset_id},
            ]
        })
        mock_table.delete_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Invalidating cache by dataset ID
        await cache_service.invalidate_by_dataset(dataset_id)

        # Then: Query should be called with correct index and delete_item should be called for each item
        assert mock_table.query.called
        query_kwargs = mock_table.query.call_args[1]
        assert "IndexName" in query_kwargs
        assert query_kwargs["IndexName"] == "dataset_id-index"

        # Verify delete_item was called twice
        assert mock_table.delete_item.call_count == 2

    @pytest.mark.asyncio
    async def test_immutability_get_does_not_affect_original(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that modifying returned dict from get() does not affect cached data."""
        # Given: Cached HTML content and mocked DynamoDB
        cache_key = "immutable_test"
        html_content = "<div>Original</div>"
        dataset_id = "dataset_123"

        current_time = int(time.time())
        mock_table = AsyncMock()
        mock_table.get_item = AsyncMock(return_value={
            "Item": {
                "cache_key": cache_key,
                "html": html_content,
                "dataset_id": dataset_id,
                "created_at": current_time,
                "ttl": current_time + 3600,
            }
        })
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Getting cache, modifying returned dict, then getting again
        result1 = await cache_service.get(cache_key)
        assert result1 is not None

        # Modify the returned dict
        result1["html"] = "<div>Modified</div>"

        # Get cache second time
        result2 = await cache_service.get(cache_key)
        assert result2 is not None

        # Then: Original cached data should be unchanged
        assert result2["html"] == html_content

    @pytest.mark.asyncio
    async def test_set_with_empty_html_caches_successfully(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that set caches successfully with empty HTML string."""
        # Given: Empty HTML string (0 bytes)
        cache_key = "empty_html_key"
        html_content = ""
        dataset_id = "dataset_123"
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Setting cache with empty HTML
        await cache_service.set(cache_key, html_content, dataset_id)

        # Then: put_item should be called successfully
        assert mock_table.put_item.called
        call_args = mock_table.put_item.call_args[1]
        assert call_args["Item"]["html"] == ""

    @pytest.mark.asyncio
    async def test_set_with_min_size_html_caches_successfully(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that set caches successfully with minimum size HTML (1 character)."""
        # Given: HTML with 1 character (1 byte)
        cache_key = "min_size_key"
        html_content = "x"
        dataset_id = "dataset_123"
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Setting cache with 1-byte HTML
        await cache_service.set(cache_key, html_content, dataset_id)

        # Then: put_item should be called successfully
        assert mock_table.put_item.called
        call_args = mock_table.put_item.call_args[1]
        assert call_args["Item"]["html"] == "x"

    @pytest.mark.asyncio
    async def test_set_with_max_minus_one_size_caches_successfully(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that set caches successfully with HTML size at MAX_CACHE_BYTES - 1."""
        # Given: HTML with size exactly MAX_CACHE_BYTES - 1 bytes
        cache_key = "max_minus_one_key"
        html_content = "x" * (cache_service.MAX_CACHE_BYTES - 1)
        dataset_id = "dataset_123"
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Setting cache with MAX_CACHE_BYTES - 1 bytes HTML
        await cache_service.set(cache_key, html_content, dataset_id)

        # Then: put_item should be called successfully
        assert mock_table.put_item.called
        call_args = mock_table.put_item.call_args[1]
        assert len(call_args["Item"]["html"].encode('utf-8')) == cache_service.MAX_CACHE_BYTES - 1

    @pytest.mark.asyncio
    async def test_set_with_max_size_skips_caching(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that set skips caching when HTML size is exactly at MAX_CACHE_BYTES."""
        # Given: HTML with size exactly MAX_CACHE_BYTES bytes
        cache_key = "max_size_key"
        html_content = "x" * cache_service.MAX_CACHE_BYTES
        dataset_id = "dataset_123"
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Setting cache with MAX_CACHE_BYTES bytes HTML
        await cache_service.set(cache_key, html_content, dataset_id)

        # Then: put_item should not be called (caching skipped)
        assert not mock_table.put_item.called

    @pytest.mark.asyncio
    async def test_set_with_max_plus_one_size_skips_caching(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that set skips caching when HTML size exceeds MAX_CACHE_BYTES."""
        # Given: HTML with size MAX_CACHE_BYTES + 1 bytes
        cache_key = "max_plus_one_key"
        html_content = "x" * (cache_service.MAX_CACHE_BYTES + 1)
        dataset_id = "dataset_123"
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Setting cache with MAX_CACHE_BYTES + 1 bytes HTML
        await cache_service.set(cache_key, html_content, dataset_id)

        # Then: put_item should not be called
        assert not mock_table.put_item.called

    @pytest.mark.asyncio
    async def test_set_with_none_html_raises_type_error(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that set raises TypeError when html is None."""
        # Given: None as html parameter
        cache_key = "none_html_key"
        html_content = None  # type: ignore
        dataset_id = "dataset_123"
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock(return_value={})
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Setting cache with None HTML
        # Then: TypeError should be raised with appropriate message
        with pytest.raises(TypeError, match="html parameter cannot be None"):
            await cache_service.set(cache_key, html_content, dataset_id)

    @pytest.mark.asyncio
    async def test_set_handles_client_error_on_put_item(
        self, cache_service: CardCacheService
    ) -> None:
        """Test that set handles ClientError from DynamoDB put_item gracefully."""
        # Given: Valid HTML and DynamoDB put_item raising ClientError
        from botocore.exceptions import ClientError
        cache_key = "client_error_key"
        html_content = "<div>Test HTML</div>"
        dataset_id = "dataset_123"
        mock_table = AsyncMock()
        error_response = {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "Rate exceeded"}}
        mock_table.put_item = AsyncMock(side_effect=ClientError(error_response, "PutItem"))
        cache_service.dynamodb.Table = MagicMock(return_value=mock_table)

        # When: Setting cache and DynamoDB raises ClientError
        await cache_service.set(cache_key, html_content, dataset_id)

        # Then: No exception should be raised, put_item should have been called
        assert mock_table.put_item.called
        # Verify the error was handled gracefully (method completed without raising)


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
    service = CardExecutionService(dynamodb=mock_dynamodb)
    service._get_dataset_rows = AsyncMock(return_value=[])
    return service


class TestCardExecutionService:
    """Test suite for CardExecutionService."""

    @pytest.mark.asyncio
    async def test_execute_cache_hit(
        self,
        execution_service: CardExecutionService,
        mock_cache_service: MagicMock,
    ) -> None:
        """Test execute returns cached result when cache hit."""
        # Given: Card execution parameters and cache service returning cached HTML
        card_id = "card_123"
        filters = {"category": "A"}
        dataset_updated_at = "2026-01-31T10:00:00Z"
        dataset_id = "dataset_123"

        cached_html = "<div>Cached HTML</div>"
        mock_cache_service.get.return_value = {
            "html": cached_html,
            "dataset_id": dataset_id,
        }

        # When: Executing card with cache enabled and cache hit
        result = await execution_service.execute(
            card_id=card_id,
            filters=filters,
            dataset_updated_at=dataset_updated_at,
            dataset_id=dataset_id,
            use_cache=True,
            cache_service=mock_cache_service,
        )

        # Then: Result should contain cached HTML and cached flag should be True
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
        # Given: Card execution parameters, cache miss, and mocked Executor API response
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

            # When: Executing card with cache enabled but cache miss
            result = await execution_service.execute(
                card_id=card_id,
                filters=filters,
                dataset_updated_at=dataset_updated_at,
                dataset_id=dataset_id,
                use_cache=True,
                cache_service=mock_cache_service,
            )

            # Then: Result should contain executor response data and cached flag should be False
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
        # Given: Card execution parameters with use_cache=False and mocked Executor API
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

            # When: Executing card with use_cache=False
            result = await execution_service.execute(
                card_id=card_id,
                filters=filters,
                dataset_updated_at=dataset_updated_at,
                dataset_id=dataset_id,
                use_cache=False,
                cache_service=mock_cache_service,
            )

            # Then: Cache should not be accessed and result should not be cached
            assert result.cached is False
            mock_cache_service.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_handles_timeout(
        self,
        execution_service: CardExecutionService,
        mock_cache_service: MagicMock,
    ) -> None:
        """Test execute handles Executor timeout."""
        # Given: Card execution parameters, cache miss, and Executor API raising timeout
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

            # When: Executing card and Executor times out after retries
            # Then: RuntimeError should be raised with appropriate message
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
        # Given: Card execution parameters, cache miss, and Executor API returning 500 error
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

            # When: Executing card and Executor returns server error after retries
            # Then: RuntimeError should be raised with appropriate message
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
        # Given: Card execution parameters, cache miss, and successful Executor API response
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

            # When: Executing card with cache enabled and cache miss
            await execution_service.execute(
                card_id=card_id,
                filters=filters,
                dataset_updated_at=dataset_updated_at,
                dataset_id=dataset_id,
                use_cache=True,
                cache_service=mock_cache_service,
            )

            # Then: Cache.set should be called to save the result
            mock_cache_service.set.assert_called_once()

    def test_card_execution_result_immutability(self) -> None:
        """Test CardExecutionResult is immutable (frozen dataclass)."""
        # Given: CardExecutionResult instance with all fields set
        result = CardExecutionResult(
            html="<div>Test</div>",
            used_columns=["col1"],
            filter_applicable=True,
            cached=False,
            execution_time_ms=100,
        )

        # When: Attempting to modify a field
        # Then: AttributeError or Exception should be raised
        with pytest.raises((AttributeError, Exception)):
            result.html = "<div>Modified</div>"  # type: ignore
