"""Tests for chat models."""
import pytest
from pydantic import ValidationError

from app.models.chat import ChatMessage, ChatRequest


class TestChatMessage:
    """Test ChatMessage model."""

    def test_create_user_message(self):
        """Test ChatMessage instantiation with role='user'."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_create_assistant_message(self):
        """Test ChatMessage instantiation with role='assistant'."""
        msg = ChatMessage(role="assistant", content="Hi there")
        assert msg.role == "assistant"
        assert msg.content == "Hi there"

    def test_invalid_role_rejected(self):
        """Test that roles other than 'user' and 'assistant' are rejected."""
        with pytest.raises(ValidationError):
            ChatMessage(role="system", content="not allowed")

    def test_invalid_role_arbitrary_string(self):
        """Test that an arbitrary string role is rejected."""
        with pytest.raises(ValidationError):
            ChatMessage(role="admin", content="not allowed")

    def test_empty_content_allowed(self):
        """Test that empty string content is accepted."""
        msg = ChatMessage(role="user", content="")
        assert msg.content == ""

    def test_missing_role_rejected(self):
        """Test that missing role field raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatMessage(content="no role")  # type: ignore

    def test_missing_content_rejected(self):
        """Test that missing content field raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatMessage(role="user")  # type: ignore

    def test_serialization(self):
        """Test ChatMessage serialization to dict."""
        msg = ChatMessage(role="user", content="test message")
        data = msg.model_dump()
        assert data == {"role": "user", "content": "test message"}


class TestChatRequest:
    """Test ChatRequest model."""

    def test_create_with_empty_history(self):
        """Test ChatRequest with an empty conversation history."""
        req = ChatRequest(message="Hello", conversation_history=[])
        assert req.message == "Hello"
        assert req.conversation_history == []

    def test_create_with_history(self):
        """Test ChatRequest with a populated conversation history."""
        history = [
            ChatMessage(role="user", content="Hi"),
            ChatMessage(role="assistant", content="Hello!"),
        ]
        req = ChatRequest(message="How are you?", conversation_history=history)
        assert req.message == "How are you?"
        assert len(req.conversation_history) == 2
        assert req.conversation_history[0].role == "user"
        assert req.conversation_history[1].role == "assistant"

    def test_history_type_validation(self):
        """Test that conversation_history rejects non-ChatMessage items."""
        with pytest.raises(ValidationError):
            ChatRequest(
                message="Hi",
                conversation_history=[{"role": "invalid_role", "content": "bad"}],
            )

    def test_history_accepts_dict_with_valid_data(self):
        """Test that conversation_history accepts dicts that conform to ChatMessage schema."""
        req = ChatRequest(
            message="Hi",
            conversation_history=[{"role": "user", "content": "hello"}],
        )
        assert isinstance(req.conversation_history[0], ChatMessage)
        assert req.conversation_history[0].role == "user"

    def test_missing_message_rejected(self):
        """Test that missing message field raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatRequest(conversation_history=[])  # type: ignore

    def test_serialization(self):
        """Test ChatRequest serialization to dict."""
        req = ChatRequest(
            message="test",
            conversation_history=[
                ChatMessage(role="user", content="hi"),
            ],
        )
        data = req.model_dump()
        assert data == {
            "message": "test",
            "conversation_history": [
                {"role": "user", "content": "hi"},
            ],
        }
