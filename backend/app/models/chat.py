"""Chat models for AI conversation."""
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=10000)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(min_length=1, max_length=10000)
    conversation_history: list[ChatMessage] = Field(default_factory=list)
