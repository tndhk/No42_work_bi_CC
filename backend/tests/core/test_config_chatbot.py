"""Chatbot config tests following TDD.

Tests for Vertex AI and chatbot-related settings in Settings class.
Each test verifies that configuration fields exist, have correct defaults,
correct types, and can be overridden via constructor (simulating env vars).
"""
import os
from unittest.mock import patch

from app.core.config import Settings


class TestChatbotConfigDefaults:
    """Test that all chatbot/Vertex AI fields have correct default values."""

    def test_vertex_ai_project_id_defaults_to_empty_string(self):
        """vertex_ai_project_id defaults to empty string for dev environments."""
        s = Settings()
        assert s.vertex_ai_project_id == ""

    def test_vertex_ai_location_default(self):
        """vertex_ai_location defaults to 'us-central1'."""
        s = Settings(vertex_ai_project_id="test-project")
        assert s.vertex_ai_location == "us-central1"

    def test_vertex_ai_model_default(self):
        """vertex_ai_model defaults to 'gemini-1.5-pro'."""
        s = Settings(vertex_ai_project_id="test-project")
        assert s.vertex_ai_model == "gemini-1.5-pro"

    def test_chatbot_rate_limit_user_default(self):
        """chatbot_rate_limit_user defaults to 5."""
        s = Settings(vertex_ai_project_id="test-project")
        assert s.chatbot_rate_limit_user == 5

    def test_chatbot_rate_limit_dashboard_default(self):
        """chatbot_rate_limit_dashboard defaults to 10."""
        s = Settings(vertex_ai_project_id="test-project")
        assert s.chatbot_rate_limit_dashboard == 10

    def test_chatbot_max_history_messages_default(self):
        """chatbot_max_history_messages defaults to 5."""
        s = Settings(vertex_ai_project_id="test-project")
        assert s.chatbot_max_history_messages == 5

    def test_chatbot_max_output_tokens_default(self):
        """chatbot_max_output_tokens defaults to 1024."""
        s = Settings(vertex_ai_project_id="test-project")
        assert s.chatbot_max_output_tokens == 1024

    def test_chatbot_temperature_default(self):
        """chatbot_temperature defaults to 0.7."""
        s = Settings(vertex_ai_project_id="test-project")
        assert s.chatbot_temperature == 0.7


class TestChatbotConfigOverrides:
    """Test that all chatbot/Vertex AI fields can be overridden."""

    def test_vertex_ai_project_id_override(self):
        """vertex_ai_project_id can be set via constructor."""
        s = Settings(vertex_ai_project_id="my-gcp-project")
        assert s.vertex_ai_project_id == "my-gcp-project"

    def test_vertex_ai_location_override(self):
        """vertex_ai_location can be overridden."""
        s = Settings(
            vertex_ai_project_id="test-project",
            vertex_ai_location="asia-northeast1",
        )
        assert s.vertex_ai_location == "asia-northeast1"

    def test_vertex_ai_model_override(self):
        """vertex_ai_model can be overridden."""
        s = Settings(
            vertex_ai_project_id="test-project",
            vertex_ai_model="gemini-2.0-flash",
        )
        assert s.vertex_ai_model == "gemini-2.0-flash"

    def test_chatbot_rate_limit_user_override(self):
        """chatbot_rate_limit_user can be overridden."""
        s = Settings(
            vertex_ai_project_id="test-project",
            chatbot_rate_limit_user=20,
        )
        assert s.chatbot_rate_limit_user == 20

    def test_chatbot_rate_limit_dashboard_override(self):
        """chatbot_rate_limit_dashboard can be overridden."""
        s = Settings(
            vertex_ai_project_id="test-project",
            chatbot_rate_limit_dashboard=50,
        )
        assert s.chatbot_rate_limit_dashboard == 50

    def test_chatbot_max_history_messages_override(self):
        """chatbot_max_history_messages can be overridden."""
        s = Settings(
            vertex_ai_project_id="test-project",
            chatbot_max_history_messages=20,
        )
        assert s.chatbot_max_history_messages == 20

    def test_chatbot_max_output_tokens_override(self):
        """chatbot_max_output_tokens can be overridden."""
        s = Settings(
            vertex_ai_project_id="test-project",
            chatbot_max_output_tokens=4096,
        )
        assert s.chatbot_max_output_tokens == 4096

    def test_chatbot_temperature_override(self):
        """chatbot_temperature can be overridden."""
        s = Settings(
            vertex_ai_project_id="test-project",
            chatbot_temperature=0.3,
        )
        assert s.chatbot_temperature == 0.3


class TestChatbotConfigFromEnvVars:
    """Test that fields can be loaded from environment variables."""

    def test_vertex_ai_project_id_from_env(self):
        """vertex_ai_project_id reads from VERTEX_AI_PROJECT_ID env var (str type representative)."""
        with patch.dict(os.environ, {"VERTEX_AI_PROJECT_ID": "env-project-id"}):
            s = Settings()
            assert s.vertex_ai_project_id == "env-project-id"

    def test_chatbot_rate_limit_user_from_env(self):
        """chatbot_rate_limit_user reads from CHATBOT_RATE_LIMIT_USER env var (int type representative)."""
        with patch.dict(os.environ, {
            "VERTEX_AI_PROJECT_ID": "test-project",
            "CHATBOT_RATE_LIMIT_USER": "15",
        }):
            s = Settings()
            assert s.chatbot_rate_limit_user == 15

    def test_chatbot_temperature_from_env(self):
        """chatbot_temperature reads from CHATBOT_TEMPERATURE env var (float type representative)."""
        with patch.dict(os.environ, {
            "VERTEX_AI_PROJECT_ID": "test-project",
            "CHATBOT_TEMPERATURE": "0.9",
        }):
            s = Settings()
            assert s.chatbot_temperature == 0.9
