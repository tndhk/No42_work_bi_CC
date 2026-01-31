"""Tests for executor client retry logic in CardExecutionService."""
import asyncio
from typing import Any
from unittest.mock import MagicMock, AsyncMock, patch

import httpx
import pytest

from app.services.card_execution_service import (
    CardExecutionService,
    CardCacheService,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
)


@pytest.fixture
def mock_dynamodb() -> Any:
    """Create mock DynamoDB resource."""
    mock_table = MagicMock()
    mock_dynamodb_resource = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    return mock_dynamodb_resource


@pytest.fixture
def execution_service(mock_dynamodb: Any) -> CardExecutionService:
    return CardExecutionService(dynamodb=mock_dynamodb)


@pytest.fixture
def mock_cache_service() -> MagicMock:
    cache = MagicMock(spec=CardCacheService)
    cache.get.return_value = None
    cache.generate_cache_key.return_value = "testcachekey1234"
    return cache


def _make_mock_client(responses):
    """Create mock httpx AsyncClient with a sequence of responses/exceptions."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=responses)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestExecutorRetryLogic:
    """Test retry logic in _execute_with_retry."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self, execution_service):
        """成功時はリトライなしで1回で完了"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "html": "<div>OK</div>",
            "used_columns": [],
            "filter_applicable": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = _make_mock_client([mock_response])

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await execution_service._execute_with_retry(
                card_id="c1", code="code", filters={}, dataset_id="ds1"
            )
            assert result["html"] == "<div>OK</div>"
            assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, execution_service):
        """TimeoutExceptionでリトライし、最終的に成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "html": "<div>Retry OK</div>",
            "used_columns": [],
            "filter_applicable": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = _make_mock_client([
            httpx.TimeoutException("timeout"),
            mock_response,
        ])

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            result = await execution_service._execute_with_retry(
                card_id="c1", code="code", filters={}, dataset_id="ds1"
            )
            assert result["html"] == "<div>Retry OK</div>"
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_5xx_error(self, execution_service):
        """5xxエラーでリトライし、最終的に成功"""
        mock_500_response = MagicMock()
        mock_500_response.status_code = 500
        mock_500_response.text = "Internal Server Error"
        http_error = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=mock_500_response
        )
        mock_500_response.raise_for_status.side_effect = http_error

        mock_ok_response = MagicMock()
        mock_ok_response.json.return_value = {
            "html": "<div>OK after 500</div>",
            "used_columns": [],
            "filter_applicable": [],
        }
        mock_ok_response.raise_for_status = MagicMock()

        mock_client = _make_mock_client([mock_500_response, mock_ok_response])

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            result = await execution_service._execute_with_retry(
                card_id="c1", code="code", filters={}, dataset_id="ds1"
            )
            assert result["html"] == "<div>OK after 500</div>"

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_error(self, execution_service):
        """4xxエラーではリトライせず即座にRuntimeError"""
        mock_400_response = MagicMock()
        mock_400_response.status_code = 400
        mock_400_response.text = "Bad Request"
        http_error = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=mock_400_response
        )
        mock_400_response.raise_for_status.side_effect = http_error

        mock_client = _make_mock_client([mock_400_response])

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="client error"):
                await execution_service._execute_with_retry(
                    card_id="c1", code="code", filters={}, dataset_id="ds1"
                )
            assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self, execution_service):
        """MAX_RETRIES回全て失敗するとRuntimeError"""
        mock_client = _make_mock_client(
            [httpx.TimeoutException("timeout")] * MAX_RETRIES
        )

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match=f"after {MAX_RETRIES} attempts"):
                await execution_service._execute_with_retry(
                    card_id="c1", code="code", filters={}, dataset_id="ds1"
                )
            assert mock_client.post.call_count == MAX_RETRIES

    @pytest.mark.asyncio
    async def test_sends_code_field(self, execution_service):
        """リクエストにcodeフィールドが含まれる"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "html": "<div>OK</div>",
            "used_columns": [],
            "filter_applicable": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = _make_mock_client([mock_response])

        with patch("httpx.AsyncClient", return_value=mock_client):
            await execution_service._execute_with_retry(
                card_id="c1",
                code="def render(d,f,p): return '<div></div>'",
                filters={"cat": "A"},
                dataset_id="ds1",
            )

            call_args = mock_client.post.call_args
            sent_json = call_args[1]["json"]
            assert "code" in sent_json
            assert sent_json["code"] == "def render(d,f,p): return '<div></div>'"
            assert sent_json["card_id"] == "c1"
            assert sent_json["dataset_id"] == "ds1"
            assert sent_json["filters"] == {"cat": "A"}

    @pytest.mark.asyncio
    async def test_execute_with_code_parameter(
        self, execution_service, mock_cache_service
    ):
        """execute() にcode引数を渡すと_execute_with_retryに渡される"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "html": "<div>Code OK</div>",
            "used_columns": ["col1"],
            "filter_applicable": False,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = _make_mock_client([mock_response])

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await execution_service.execute(
                card_id="c1",
                filters={},
                dataset_updated_at="2024-01-01",
                dataset_id="ds1",
                use_cache=False,
                cache_service=mock_cache_service,
                code="def render(d,f,p): return '<div>Code OK</div>'",
            )
            assert result.html == "<div>Code OK</div>"
            assert result.cached is False

    @pytest.mark.asyncio
    async def test_retry_on_connect_error(self, execution_service):
        """ConnectErrorでリトライ"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "html": "<div>Connected</div>",
            "used_columns": [],
            "filter_applicable": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = _make_mock_client([
            httpx.ConnectError("connection refused"),
            mock_response,
        ])

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            result = await execution_service._execute_with_retry(
                card_id="c1", code="code", filters={}, dataset_id="ds1"
            )
            assert result["html"] == "<div>Connected</div>"
