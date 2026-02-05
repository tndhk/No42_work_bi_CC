"""Tests for ChatbotService - system prompt construction, SSE formatting, and streaming."""
import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.models.chat import ChatMessage
from app.services.chatbot_service import ChatbotService, format_sse_event


@pytest.fixture
def default_settings() -> Settings:
    """Create Settings with default values for testing."""
    return Settings(
        vertex_ai_project_id="test-project",
        vertex_ai_location="us-central1",
        vertex_ai_model="gemini-1.5-pro",
        chatbot_max_output_tokens=1024,
        chatbot_temperature=0.7,
    )


@pytest.fixture
def service(default_settings: Settings) -> ChatbotService:
    """Create a ChatbotService instance for testing."""
    return ChatbotService(settings=default_settings)


class TestChatbotServiceInit:
    """Test ChatbotService initialization."""

    def test_init_stores_settings(self, default_settings: Settings):
        """ChatbotService should store the provided settings."""
        svc = ChatbotService(settings=default_settings)
        assert svc.settings is default_settings

    def test_init_with_custom_settings(self):
        """ChatbotService should accept custom settings values."""
        custom = Settings(
            vertex_ai_project_id="custom-project",
            vertex_ai_location="asia-northeast1",
            vertex_ai_model="gemini-2.0-flash",
            chatbot_temperature=0.3,
        )
        svc = ChatbotService(settings=custom)
        assert svc.settings.vertex_ai_project_id == "custom-project"
        assert svc.settings.vertex_ai_location == "asia-northeast1"
        assert svc.settings.vertex_ai_model == "gemini-2.0-flash"
        assert svc.settings.chatbot_temperature == 0.3


class TestBuildSystemPrompt:
    """Test _build_system_prompt method."""

    def test_contains_assistant_role(self, service: ChatbotService):
        """System prompt should declare the assistant as a data analysis assistant."""
        prompt = service._build_system_prompt(
            dashboard_name="Sales Dashboard",
            dataset_texts=[]
        )
        assert "データ分析アシスタント" in prompt

    def test_contains_dashboard_name(self, service: ChatbotService):
        """System prompt should include the dashboard name."""
        prompt = service._build_system_prompt(
            dashboard_name="Monthly Revenue Report",
            dataset_texts=[]
        )
        assert "Monthly Revenue Report" in prompt

    def test_contains_dataset_information(self, service: ChatbotService):
        """System prompt should include each dataset text."""
        datasets = [
            "Dataset: Sales Data (1000 rows) - columns: id, amount, date",
            "Dataset: Customer Data (500 rows) - columns: id, name, email",
        ]
        prompt = service._build_system_prompt(
            dashboard_name="Test Dashboard",
            dataset_texts=datasets
        )
        assert "Sales Data (1000 rows)" in prompt
        assert "Customer Data (500 rows)" in prompt

    def test_contains_data_based_response_instruction(self, service: ChatbotService):
        """System prompt should instruct to provide data-based answers."""
        prompt = service._build_system_prompt(
            dashboard_name="Test Dashboard",
            dataset_texts=[]
        )
        assert "データに基づ" in prompt

    def test_empty_dataset_texts(self, service: ChatbotService):
        """System prompt should handle empty dataset list gracefully."""
        prompt = service._build_system_prompt(
            dashboard_name="Empty Dashboard",
            dataset_texts=[]
        )
        # Should still be a valid prompt with the role and dashboard name
        assert "データ分析アシスタント" in prompt
        assert "Empty Dashboard" in prompt

    def test_single_dataset(self, service: ChatbotService):
        """System prompt should work with a single dataset."""
        prompt = service._build_system_prompt(
            dashboard_name="Single Dataset Dashboard",
            dataset_texts=["Dataset: Orders (200 rows) - columns: order_id, total"]
        )
        assert "Orders (200 rows)" in prompt

    def test_multiple_datasets(self, service: ChatbotService):
        """System prompt should include all datasets when multiple are provided."""
        datasets = [
            "Dataset: A (10 rows)",
            "Dataset: B (20 rows)",
            "Dataset: C (30 rows)",
        ]
        prompt = service._build_system_prompt(
            dashboard_name="Multi Dashboard",
            dataset_texts=datasets
        )
        for ds_text in datasets:
            assert ds_text in prompt

    def test_return_type_is_string(self, service: ChatbotService):
        """_build_system_prompt should return a string."""
        prompt = service._build_system_prompt(
            dashboard_name="Test",
            dataset_texts=[]
        )
        assert isinstance(prompt, str)

    def test_prompt_is_not_empty(self, service: ChatbotService):
        """System prompt should never be empty."""
        prompt = service._build_system_prompt(
            dashboard_name="Test",
            dataset_texts=[]
        )
        assert len(prompt.strip()) > 0

    def test_special_characters_in_dashboard_name(self, service: ChatbotService):
        """System prompt should handle special characters in dashboard name."""
        prompt = service._build_system_prompt(
            dashboard_name="Dashboard <script>alert('xss')</script> & \"quotes\"",
            dataset_texts=[]
        )
        assert "Dashboard <script>alert('xss')</script> & \"quotes\"" in prompt

    def test_unicode_in_dashboard_name(self, service: ChatbotService):
        """System prompt should handle Japanese/Unicode characters."""
        prompt = service._build_system_prompt(
            dashboard_name="売上分析ダッシュボード",
            dataset_texts=["Dataset: 売上データ (1000行)"]
        )
        assert "売上分析ダッシュボード" in prompt
        assert "売上データ (1000行)" in prompt


# ============================================================================
# format_sse_event: Basic behavior
# ============================================================================


class TestFormatSseEventWithoutEventType:
    """Test SSE formatting when event type is None (default)."""

    def test_data_only_format(self) -> None:
        """data-only SSE: 'data: {data}\\n\\n' format."""
        result = format_sse_event("hello")
        assert result == "data: hello\n\n"

    def test_data_only_with_explicit_none(self) -> None:
        """Explicitly passing event=None produces data-only format."""
        result = format_sse_event("hello", event=None)
        assert result == "data: hello\n\n"

    def test_empty_data_string(self) -> None:
        """Empty string data is valid SSE."""
        result = format_sse_event("")
        assert result == "data: \n\n"


class TestFormatSseEventWithEventType:
    """Test SSE formatting when event type is specified."""

    def test_token_event(self) -> None:
        """Token event: partial text streaming."""
        result = format_sse_event("partial text", event="token")
        assert result == "event: token\ndata: partial text\n\n"

    def test_done_event(self) -> None:
        """Done event: sources information."""
        result = format_sse_event('{"sources": []}', event="done")
        assert result == 'event: done\ndata: {"sources": []}\n\n'

    def test_error_event(self) -> None:
        """Error event: error message."""
        result = format_sse_event("Something went wrong", event="error")
        assert result == "event: error\ndata: Something went wrong\n\n"

    def test_custom_event_type(self) -> None:
        """Arbitrary event type string is supported."""
        result = format_sse_event("payload", event="custom")
        assert result == "event: custom\ndata: payload\n\n"


# ============================================================================
# format_sse_event: Edge cases
# ============================================================================


class TestFormatSseEventEdgeCases:
    """Test edge cases and special data content."""

    def test_data_with_json_content(self) -> None:
        """JSON string as data is preserved as-is."""
        json_data = '{"key": "value", "count": 42}'
        result = format_sse_event(json_data, event="done")
        assert result == f"event: done\ndata: {json_data}\n\n"

    def test_data_with_unicode(self) -> None:
        """Unicode characters in data are preserved."""
        result = format_sse_event("日本語テスト", event="token")
        assert result == "event: token\ndata: 日本語テスト\n\n"

    def test_data_with_special_characters(self) -> None:
        """Special characters (angle brackets, ampersands) are preserved."""
        result = format_sse_event("<script>alert('xss')</script>", event="token")
        assert result == "event: token\ndata: <script>alert('xss')</script>\n\n"

    def test_data_with_spaces(self) -> None:
        """Data with leading/trailing spaces is preserved."""
        result = format_sse_event("  spaced  ", event="token")
        assert result == "event: token\ndata:   spaced  \n\n"

    def test_return_type_is_str(self) -> None:
        """Return value is always a string."""
        result = format_sse_event("test")
        assert isinstance(result, str)

    def test_result_ends_with_double_newline(self) -> None:
        """SSE spec requires events to end with double newline."""
        result_no_event = format_sse_event("data1")
        result_with_event = format_sse_event("data2", event="token")
        assert result_no_event.endswith("\n\n")
        assert result_with_event.endswith("\n\n")


# ============================================================================
# stream_chat: Vertex AI streaming via mocked SDK
# ============================================================================


def _make_chunk(text: str) -> MagicMock:
    """Create a mock Vertex AI response chunk with the given text."""
    chunk = MagicMock()
    chunk.text = text
    return chunk


def _make_stream_response(chunks: list[MagicMock]) -> MagicMock:
    """Create a mock streaming response that iterates over chunks."""
    response = MagicMock()
    response.__iter__ = MagicMock(return_value=iter(chunks))
    return response


class TestStreamChatBasic:
    """Test stream_chat yields tokens from Vertex AI."""

    @pytest.mark.asyncio
    async def test_yields_tokens_from_vertex_ai(
        self, service: ChatbotService
    ) -> None:
        """stream_chat should yield each token chunk from Vertex AI."""
        chunks = [_make_chunk("Hello"), _make_chunk(" world"), _make_chunk("!")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            tokens = []
            async for token in service.stream_chat(
                dashboard_name="Test Dashboard",
                dataset_texts=["Dataset: Sales (100 rows)"],
                message="Show me the summary",
                conversation_history=[],
            ):
                tokens.append(token)

        assert tokens == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_yields_single_token(self, service: ChatbotService) -> None:
        """stream_chat should handle a single-chunk response."""
        chunks = [_make_chunk("Only one chunk")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            tokens = []
            async for token in service.stream_chat(
                dashboard_name="Dashboard",
                dataset_texts=[],
                message="Hello",
                conversation_history=[],
            ):
                tokens.append(token)

        assert tokens == ["Only one chunk"]

    @pytest.mark.asyncio
    async def test_empty_response_yields_nothing(
        self, service: ChatbotService
    ) -> None:
        """stream_chat should yield nothing for empty response."""
        mock_stream = _make_stream_response([])

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            tokens = []
            async for token in service.stream_chat(
                dashboard_name="Dashboard",
                dataset_texts=[],
                message="Hello",
                conversation_history=[],
            ):
                tokens.append(token)

        assert tokens == []


class TestStreamChatHistoryTruncation:
    """Test that conversation_history is truncated to max_history_messages."""

    @pytest.mark.asyncio
    async def test_truncates_history_to_max(self) -> None:
        """History longer than chatbot_max_history_messages should be truncated."""
        settings = Settings(
            vertex_ai_project_id="test-project",
            vertex_ai_location="us-central1",
            vertex_ai_model="gemini-1.5-pro",
            chatbot_max_history_messages=3,
            chatbot_max_output_tokens=1024,
            chatbot_temperature=0.7,
        )
        svc = ChatbotService(settings=settings)

        history = [
            ChatMessage(role="user", content=f"msg-{i}")
            for i in range(10)
        ]

        chunks = [_make_chunk("ok")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            tokens = []
            async for token in svc.stream_chat(
                dashboard_name="Test",
                dataset_texts=[],
                message="latest",
                conversation_history=history,
            ):
                tokens.append(token)

        # Verify generate_content was called
        mock_model.generate_content.assert_called_once()

        # Check the contents passed contain only last 3 history messages + current
        call_args = mock_model.generate_content.call_args
        contents = call_args[0][0] if call_args[0] else call_args[1].get("contents")

        # The contents list should have:
        # - system instruction is passed separately
        # - 3 history messages (truncated from 10) + 1 current user message = 4
        # Count Content objects that represent messages
        assert len(contents) == 4  # 3 history + 1 current

    @pytest.mark.asyncio
    async def test_history_within_limit_not_truncated(self) -> None:
        """History within limit should be passed through unchanged."""
        settings = Settings(
            vertex_ai_project_id="test-project",
            vertex_ai_location="us-central1",
            vertex_ai_model="gemini-1.5-pro",
            chatbot_max_history_messages=5,
            chatbot_max_output_tokens=1024,
            chatbot_temperature=0.7,
        )
        svc = ChatbotService(settings=settings)

        history = [
            ChatMessage(role="user", content="Q1"),
            ChatMessage(role="assistant", content="A1"),
        ]

        chunks = [_make_chunk("response")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            tokens = []
            async for token in svc.stream_chat(
                dashboard_name="Test",
                dataset_texts=[],
                message="Q2",
                conversation_history=history,
            ):
                tokens.append(token)

        call_args = mock_model.generate_content.call_args
        contents = call_args[0][0] if call_args[0] else call_args[1].get("contents")
        # 2 history + 1 current = 3
        assert len(contents) == 3

    @pytest.mark.asyncio
    async def test_empty_history(self) -> None:
        """Empty history should result in only the current message."""
        settings = Settings(
            vertex_ai_project_id="test-project",
            vertex_ai_location="us-central1",
            vertex_ai_model="gemini-1.5-pro",
            chatbot_max_history_messages=5,
            chatbot_max_output_tokens=1024,
            chatbot_temperature=0.7,
        )
        svc = ChatbotService(settings=settings)

        chunks = [_make_chunk("response")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            tokens = []
            async for token in svc.stream_chat(
                dashboard_name="Test",
                dataset_texts=[],
                message="Hello",
                conversation_history=[],
            ):
                tokens.append(token)

        call_args = mock_model.generate_content.call_args
        contents = call_args[0][0] if call_args[0] else call_args[1].get("contents")
        # Only the current message
        assert len(contents) == 1


class TestStreamChatModelConfiguration:
    """Test that Vertex AI model is configured with correct parameters."""

    @pytest.mark.asyncio
    async def test_uses_correct_model_name(self, service: ChatbotService) -> None:
        """GenerativeModel should be initialized with settings.vertex_ai_model."""
        chunks = [_make_chunk("ok")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ) as mock_cls:
            async for _ in service.stream_chat(
                dashboard_name="Test",
                dataset_texts=[],
                message="Hi",
                conversation_history=[],
            ):
                pass

        mock_cls.assert_called_once_with("gemini-1.5-pro")

    @pytest.mark.asyncio
    async def test_passes_stream_true(self, service: ChatbotService) -> None:
        """generate_content should be called with stream=True."""
        chunks = [_make_chunk("ok")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            async for _ in service.stream_chat(
                dashboard_name="Test",
                dataset_texts=[],
                message="Hi",
                conversation_history=[],
            ):
                pass

        call_kwargs = mock_model.generate_content.call_args[1]
        assert call_kwargs.get("stream") is True

    @pytest.mark.asyncio
    async def test_passes_temperature_from_settings(
        self, service: ChatbotService
    ) -> None:
        """generate_content should use settings.chatbot_temperature."""
        chunks = [_make_chunk("ok")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            async for _ in service.stream_chat(
                dashboard_name="Test",
                dataset_texts=[],
                message="Hi",
                conversation_history=[],
            ):
                pass

        call_kwargs = mock_model.generate_content.call_args[1]
        gen_config = call_kwargs.get("generation_config")
        assert gen_config is not None
        assert gen_config.get("temperature") == 0.7

    @pytest.mark.asyncio
    async def test_passes_max_output_tokens_from_settings(
        self, service: ChatbotService
    ) -> None:
        """generate_content should use settings.chatbot_max_output_tokens."""
        chunks = [_make_chunk("ok")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            async for _ in service.stream_chat(
                dashboard_name="Test",
                dataset_texts=[],
                message="Hi",
                conversation_history=[],
            ):
                pass

        call_kwargs = mock_model.generate_content.call_args[1]
        gen_config = call_kwargs.get("generation_config")
        assert gen_config is not None
        assert gen_config.get("max_output_tokens") == 1024

    @pytest.mark.asyncio
    async def test_passes_system_instruction(
        self, service: ChatbotService
    ) -> None:
        """generate_content should include system_instruction from _build_system_prompt."""
        chunks = [_make_chunk("ok")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            async for _ in service.stream_chat(
                dashboard_name="Sales Dashboard",
                dataset_texts=["Dataset: Sales (100 rows)"],
                message="Summarize",
                conversation_history=[],
            ):
                pass

        # Verify the model was created with system_instruction
        # OR system_instruction was passed to generate_content
        # Check the GenerativeModel constructor or generate_content kwargs
        call_kwargs = mock_model.generate_content.call_args[1]
        assert "system_instruction" in call_kwargs


class TestStreamChatVertexAIIntegration:
    """Test stream_chat uses asyncio.to_thread for sync SDK wrapping."""

    @pytest.mark.asyncio
    async def test_is_async_generator(self, service: ChatbotService) -> None:
        """stream_chat should return an async generator."""
        chunks = [_make_chunk("ok")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            gen = service.stream_chat(
                dashboard_name="Test",
                dataset_texts=[],
                message="Hi",
                conversation_history=[],
            )
            # Verify it's an async generator
            assert hasattr(gen, "__aiter__")
            assert hasattr(gen, "__anext__")
            # Consume the generator
            async for _ in gen:
                pass

    @pytest.mark.asyncio
    async def test_unicode_tokens_preserved(
        self, service: ChatbotService
    ) -> None:
        """stream_chat should correctly yield Unicode tokens."""
        chunks = [_make_chunk("売上は"), _make_chunk("100万円"), _make_chunk("です。")]
        mock_stream = _make_stream_response(chunks)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            tokens = []
            async for token in service.stream_chat(
                dashboard_name="売上ダッシュボード",
                dataset_texts=["Dataset: 売上データ"],
                message="売上を教えて",
                conversation_history=[],
            ):
                tokens.append(token)

        assert tokens == ["売上は", "100万円", "です。"]


class TestStreamChatErrorHandling:
    """Test error handling in stream_chat."""

    @pytest.mark.asyncio
    async def test_vertex_ai_exception_propagates(
        self, service: ChatbotService
    ) -> None:
        """Exceptions from Vertex AI should propagate to caller."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")

        with patch(
            "app.services.chatbot_service.GenerativeModel",
            return_value=mock_model,
        ):
            with pytest.raises(Exception, match="API Error"):
                async for _ in service.stream_chat(
                    dashboard_name="Test",
                    dataset_texts=[],
                    message="Hi",
                    conversation_history=[],
                ):
                    pass
