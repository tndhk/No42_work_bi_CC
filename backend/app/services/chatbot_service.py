"""Chatbot service for AI-powered data analysis assistance."""
import asyncio
import logging
from collections.abc import AsyncGenerator
from queue import Queue

from vertexai.generative_models import Content, GenerativeModel, Part

from app.core.config import Settings
from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


def format_sse_event(data: str, event: str | None = None) -> str:
    """Format a Server-Sent Events (SSE) message.

    Follows the SSE specification: each event ends with a double newline.
    If an event type is specified, the 'event:' field is prepended.

    Args:
        data: The data payload for the SSE message.
        event: Optional event type (e.g., 'token', 'done', 'error').

    Returns:
        A properly formatted SSE event string.
    """
    if event is not None:
        return f"event: {event}\ndata: {data}\n\n"
    return f"data: {data}\n\n"


class ChatbotService:
    """Service for chatbot interactions with dashboard data."""

    def __init__(self, settings: Settings) -> None:
        """Initialize ChatbotService.

        Args:
            settings: Application settings containing Vertex AI configuration.
        """
        self.settings = settings

    def _build_system_prompt(
        self, dashboard_name: str, dataset_texts: list[str]
    ) -> str:
        """Build the system prompt for the chatbot.

        Constructs a prompt that:
        - Declares the role as a data analysis assistant
        - Includes the dashboard name for context
        - Lists available dataset information
        - Instructs to provide data-based answers

        Args:
            dashboard_name: Name of the dashboard being analyzed.
            dataset_texts: List of dataset description strings.

        Returns:
            The constructed system prompt string.
        """
        dataset_section = ""
        if dataset_texts:
            dataset_lines = "\n".join(f"- {text}" for text in dataset_texts)
            dataset_section = (
                f"\n\n## 参照可能なデータセット\n{dataset_lines}"
            )
        else:
            dataset_section = "\n\n## 参照可能なデータセット\nなし"

        prompt = (
            f"あなたはデータ分析アシスタントです。"
            f"ダッシュボード「{dashboard_name}」に関する質問に回答します。"
            f"{dataset_section}"
            f"\n\n## 回答方針"
            f"\nユーザーの質問に対して、データに基づいた回答を提供してください。"
            f"\n具体的な数値や傾向を示し、わかりやすく説明してください。"
        )

        return prompt

    async def stream_chat(
        self,
        dashboard_name: str,
        dataset_texts: list[str],
        message: str,
        conversation_history: list[ChatMessage],
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses from Vertex AI.

        1. Builds a system prompt via _build_system_prompt().
        2. Truncates conversation_history to the most recent
           settings.chatbot_max_history_messages entries.
        3. Initializes a GenerativeModel from the Vertex AI SDK.
        4. Calls generate_content() with stream=True.
        5. Yields each text token as it arrives.

        The Vertex AI SDK's synchronous streaming iterator is wrapped
        with asyncio.to_thread so it can be consumed from async code.

        Args:
            dashboard_name: Name of the dashboard for context.
            dataset_texts: Dataset description strings for the prompt.
            message: The current user message.
            conversation_history: Previous messages in the conversation.

        Yields:
            Text tokens from the Vertex AI model response.
        """
        # 1. Build system prompt
        system_prompt = self._build_system_prompt(
            dashboard_name=dashboard_name,
            dataset_texts=dataset_texts,
        )

        # 2. Truncate history to last N messages
        max_history = self.settings.chatbot_max_history_messages
        truncated_history = conversation_history[-max_history:]

        # 3. Build contents list for Vertex AI
        contents: list[Content] = []
        for msg in truncated_history:
            role = "user" if msg.role == "user" else "model"
            contents.append(
                Content(role=role, parts=[Part.from_text(msg.content)])
            )
        # Add the current user message
        contents.append(
            Content(role="user", parts=[Part.from_text(message)])
        )

        # 4. Initialize model and call generate_content with streaming
        model = GenerativeModel(self.settings.vertex_ai_model)

        generation_config = {
            "temperature": self.settings.chatbot_temperature,
            "max_output_tokens": self.settings.chatbot_max_output_tokens,
        }

        # Run the synchronous streaming call in a thread
        response = await asyncio.to_thread(
            model.generate_content,
            contents,
            generation_config=generation_config,
            stream=True,
            system_instruction=system_prompt,
        )

        # 5. Stream tokens from the response using a queue for true SSE
        # This ensures chunks are yielded as they arrive, not batched
        def _stream_to_queue(sync_iterator, q: Queue) -> None:
            """Stream chunks from sync iterator to queue.

            Args:
                sync_iterator: The synchronous Vertex AI response iterator.
                q: Queue to transfer chunks to the async context.

            The queue protocol:
            - Normal chunks: chunk.text string
            - Errors: Exception instance
            - End-of-stream: None (sentinel)
            """
            try:
                for chunk in sync_iterator:
                    q.put(chunk.text)
                q.put(None)  # sentinel: end of stream
            except Exception as e:
                q.put(e)  # propagate error
                q.put(None)  # sentinel

        q: Queue = Queue()
        # Start streaming in background thread
        asyncio.create_task(asyncio.to_thread(_stream_to_queue, response, q))

        # Yield chunks as they arrive
        while True:
            item = await asyncio.to_thread(q.get)
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
            yield item
