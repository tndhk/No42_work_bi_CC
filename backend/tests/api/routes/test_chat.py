"""Chat API endpoint tests.

Tests for POST /api/dashboards/{dashboard_id}/chat
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.models.dashboard import Dashboard, DashboardLayout
from app.models.dashboard_share import Permission
from app.models.user import User


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    return User(
        id="user_123",
        email="test@example.com",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_dynamodb():
    """Create mock DynamoDB resource."""
    return MagicMock()


@pytest.fixture
def mock_s3():
    """Create mock S3 client."""
    return MagicMock()


@pytest.fixture
def sample_dashboard():
    """Create sample dashboard for chat tests."""
    return Dashboard(
        id="dash_chat_001",
        name="Sales Dashboard",
        description="Sales analytics",
        layout=DashboardLayout(cards=[], columns=12, row_height=100),
        filters=None,
        owner_id="user_123",
        default_filter_view_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def authenticated_client(mock_user, mock_dynamodb, mock_s3):
    """Create test client with authentication and dependency overrides."""

    async def override_get_current_user():
        return mock_user

    async def override_get_dynamodb_resource():
        yield mock_dynamodb

    async def override_get_s3_client():
        yield mock_s3

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_dynamodb_resource] = override_get_dynamodb_resource
    app.dependency_overrides[get_s3_client] = override_get_s3_client

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    """Create test client without authentication overrides."""
    return TestClient(app)


class TestChatEndpointAuth:
    """Tests for authentication and authorization of chat endpoint."""

    def test_returns_403_without_authentication(
        self, unauthenticated_client: TestClient
    ) -> None:
        """POST /{dashboard_id}/chat returns 403 when no credentials provided.

        The get_current_user dependency returns 403 for missing credentials
        in this codebase, matching the existing auth pattern.
        """
        response = unauthenticated_client.post(
            "/api/dashboards/dash_chat_001/chat",
            json={"message": "hello", "conversation_history": []},
        )
        assert response.status_code == 403

    def test_returns_403_without_viewer_permission(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """POST /{dashboard_id}/chat returns 403 when user lacks VIEWER permission."""
        async def mock_get_by_id(self, dashboard_id, dynamodb):
            return sample_dashboard

        async def mock_assert_permission(self, dashboard, user_id, required, dynamodb):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required.value} permission or higher",
            )

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            "get_by_id",
            mock_get_by_id,
        ), patch.object(
            permission_service.PermissionService,
            "assert_permission",
            mock_assert_permission,
        ):
            response = authenticated_client.post(
                "/api/dashboards/dash_chat_001/chat",
                json={"message": "hello", "conversation_history": []},
            )

            assert response.status_code == 403
            assert "permission" in response.json()["detail"].lower()


class TestChatEndpointNotFound:
    """Tests for dashboard not found scenarios."""

    def test_returns_404_when_dashboard_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """POST /{dashboard_id}/chat returns 404 when dashboard does not exist."""
        async def mock_get_by_id(self, dashboard_id, dynamodb):
            return None

        from app.repositories import dashboard_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            "get_by_id",
            mock_get_by_id,
        ):
            response = authenticated_client.post(
                "/api/dashboards/dash_nonexistent/chat",
                json={"message": "hello", "conversation_history": []},
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestChatEndpointValidation:
    """Tests for request body validation."""

    def test_returns_422_for_missing_message(
        self, authenticated_client: TestClient
    ) -> None:
        """POST /{dashboard_id}/chat returns 422 when message field is missing."""
        response = authenticated_client.post(
            "/api/dashboards/dash_chat_001/chat",
            json={"conversation_history": []},
        )
        assert response.status_code == 422

    def test_returns_422_for_invalid_body(
        self, authenticated_client: TestClient
    ) -> None:
        """POST /{dashboard_id}/chat returns 422 when body is not valid JSON."""
        response = authenticated_client.post(
            "/api/dashboards/dash_chat_001/chat",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_returns_422_for_invalid_conversation_history(
        self, authenticated_client: TestClient
    ) -> None:
        """POST /{dashboard_id}/chat returns 422 when conversation_history has invalid role."""
        response = authenticated_client.post(
            "/api/dashboards/dash_chat_001/chat",
            json={
                "message": "hello",
                "conversation_history": [
                    {"role": "invalid_role", "content": "test"}
                ],
            },
        )
        assert response.status_code == 422


class TestChatEndpointSuccess:
    """Tests for successful chat streaming response."""

    def _make_patches(self, sample_dashboard, referenced_datasets=None, summary_dict=None, tokens=None):
        """Create common patch context managers for success tests.

        Returns a list of context managers and the patched functions.
        """
        if referenced_datasets is None:
            referenced_datasets = []
        if summary_dict is None:
            summary_dict = {
                "schema": [{"name": "revenue", "dtype": "float64", "nullable": False}],
                "statistics": {"revenue": {"min": 0, "max": 100, "mean": 50.0, "std": 25.0, "null_count": 0}},
                "row_count": 1000,
                "column_count": 1,
            }
        if tokens is None:
            tokens = ["Hello", " World"]

        async def mock_get_by_id(self, dashboard_id, dynamodb):
            return sample_dashboard

        async def mock_assert_permission(self, dashboard, user_id, required, dynamodb):
            pass

        async def mock_get_referenced_datasets(self, dashboard, dynamodb):
            return referenced_datasets

        async def mock_generate_summary(self, s3_path):
            return summary_dict

        async def mock_stream_chat(self, dashboard_name, dataset_texts, message, conversation_history):
            for t in tokens:
                yield t

        async def mock_log_chatbot_query(self, user_id, dashboard_id, message, dynamodb, metadata=None, request_id=None):
            return None

        return (
            mock_get_by_id,
            mock_assert_permission,
            mock_get_referenced_datasets,
            mock_generate_summary,
            mock_stream_chat,
            mock_log_chatbot_query,
        )

    def _apply_patches(self, mocks):
        """Apply patches using the mock functions returned from _make_patches."""
        from app.repositories import dashboard_repository
        from app.services import permission_service, dashboard_service, audit_service
        from app.services import dataset_summarizer as ds_module
        from app.services import chatbot_service as cs_module

        (
            mock_get_by_id,
            mock_assert_permission,
            mock_get_referenced_datasets,
            mock_generate_summary,
            mock_stream_chat,
            mock_log_chatbot_query,
        ) = mocks

        from contextlib import ExitStack

        stack = ExitStack()
        stack.enter_context(patch.object(
            dashboard_repository.DashboardRepository, "get_by_id", mock_get_by_id
        ))
        stack.enter_context(patch.object(
            permission_service.PermissionService, "assert_permission", mock_assert_permission
        ))
        stack.enter_context(patch.object(
            dashboard_service.DashboardService, "get_referenced_datasets", mock_get_referenced_datasets
        ))
        stack.enter_context(patch.object(
            ds_module.DatasetSummarizer, "generate_summary", mock_generate_summary
        ))
        stack.enter_context(patch.object(
            cs_module.ChatbotService, "stream_chat", mock_stream_chat
        ))
        stack.enter_context(patch.object(
            audit_service.AuditService, "log_chatbot_query", mock_log_chatbot_query
        ))
        return stack

    def test_returns_200_with_sse_streaming(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """POST /{dashboard_id}/chat returns 200 with SSE streaming response."""
        mocks = self._make_patches(
            sample_dashboard,
            referenced_datasets=[
                {
                    "dataset_id": "ds_001",
                    "name": "Sales Data",
                    "row_count": 1000,
                    "used_by_cards": ["card_1"],
                }
            ],
        )

        with self._apply_patches(mocks):
            response = authenticated_client.post(
                "/api/dashboards/dash_chat_001/chat",
                json={"message": "What is the revenue trend?", "conversation_history": []},
            )

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            body = response.text
            assert "data:" in body

    def test_returns_200_with_conversation_history(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """POST /{dashboard_id}/chat handles conversation_history correctly."""
        mocks = self._make_patches(sample_dashboard, tokens=["response"])

        with self._apply_patches(mocks):
            response = authenticated_client.post(
                "/api/dashboards/dash_chat_001/chat",
                json={
                    "message": "Follow up question",
                    "conversation_history": [
                        {"role": "user", "content": "First question"},
                        {"role": "assistant", "content": "First answer"},
                    ],
                },
            )

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

    def test_sse_events_contain_done_event(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """POST /{dashboard_id}/chat SSE stream includes a done event at the end."""
        mocks = self._make_patches(sample_dashboard, tokens=["token1"])

        with self._apply_patches(mocks):
            response = authenticated_client.post(
                "/api/dashboards/dash_chat_001/chat",
                json={"message": "hi", "conversation_history": []},
            )

            assert response.status_code == 200
            body = response.text
            assert "data: token1" in body
            assert "event: done" in body

    def test_sse_events_contain_token_events(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """POST /{dashboard_id}/chat SSE stream includes token events for each chunk."""
        mocks = self._make_patches(sample_dashboard, tokens=["Hello", " World"])

        with self._apply_patches(mocks):
            response = authenticated_client.post(
                "/api/dashboards/dash_chat_001/chat",
                json={"message": "hi", "conversation_history": []},
            )

            assert response.status_code == 200
            body = response.text
            assert "event: token\ndata: Hello" in body
            assert "event: token\ndata:  World" in body


class TestChatEndpointRateLimit:
    """Tests for rate limiting on chat endpoint."""

    def test_returns_429_when_rate_limit_exceeded(
        self, mock_user, mock_dynamodb, mock_s3, sample_dashboard
    ) -> None:
        """POST /{dashboard_id}/chat returns 429 when rate limit is exceeded."""
        from app.main import app as test_app, limiter

        # Enable rate limiting for this test
        original_enabled = limiter.enabled
        limiter.enabled = True

        async def override_get_current_user():
            return mock_user

        async def override_get_dynamodb_resource():
            yield mock_dynamodb

        async def override_get_s3_client():
            yield mock_s3

        test_app.dependency_overrides[get_current_user] = override_get_current_user
        test_app.dependency_overrides[get_dynamodb_resource] = override_get_dynamodb_resource
        test_app.dependency_overrides[get_s3_client] = override_get_s3_client

        async def mock_get_by_id(self, dashboard_id, dynamodb):
            return sample_dashboard

        async def mock_assert_permission(self, dashboard, user_id, required, dynamodb):
            pass

        async def mock_get_referenced_datasets(self, dashboard, dynamodb):
            return []

        async def mock_stream_chat(self, dashboard_name, dataset_texts, message, conversation_history):
            yield "ok"

        async def mock_log_chatbot_query(self, user_id, dashboard_id, message, dynamodb, metadata=None, request_id=None):
            return None

        from app.repositories import dashboard_repository
        from app.services import permission_service, dashboard_service, audit_service
        from app.services import chatbot_service as cs_module

        try:
            with patch.object(
                dashboard_repository.DashboardRepository,
                "get_by_id",
                mock_get_by_id,
            ), patch.object(
                permission_service.PermissionService,
                "assert_permission",
                mock_assert_permission,
            ), patch.object(
                dashboard_service.DashboardService,
                "get_referenced_datasets",
                mock_get_referenced_datasets,
            ), patch.object(
                cs_module.ChatbotService,
                "stream_chat",
                mock_stream_chat,
            ), patch.object(
                audit_service.AuditService,
                "log_chatbot_query",
                mock_log_chatbot_query,
            ):
                client = TestClient(test_app)
                last_status = None
                # Send requests exceeding rate limit (5/minute)
                for i in range(7):
                    resp = client.post(
                        "/api/dashboards/dash_chat_001/chat",
                        json={"message": f"msg {i}", "conversation_history": []},
                    )
                    last_status = resp.status_code
                    if resp.status_code == 429:
                        break

                assert last_status == 429
        finally:
            limiter.enabled = original_enabled
            test_app.dependency_overrides.clear()
