"""User API endpoint tests."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource
from app.models.user import User, UserInDB


@pytest.fixture
def mock_user():
    return User(
        id="user_123",
        email="test@example.com",
        role="user",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_dynamodb():
    return MagicMock()


@pytest.fixture
def authenticated_client(mock_user, mock_dynamodb):
    async def override_get_current_user():
        return mock_user

    async def override_get_dynamodb_resource():
        yield mock_dynamodb

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_dynamodb_resource] = override_get_dynamodb_resource

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    return TestClient(app)


class TestSearchUsers:
    """Tests for GET /api/users."""

    def test_search_users_success(self, authenticated_client):
        """Test searching users by email."""
        found_users = [
            UserInDB(
                id="user_456",
                email="alice@example.com",
                hashed_password="hashed",
                role="user",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            UserInDB(
                id="user_789",
                email="alice.b@example.com",
                hashed_password="hashed",
                role="user",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

        async def mock_scan(self, query, limit, dynamodb):
            return found_users

        from app.repositories import user_repository

        with patch.object(
            user_repository.UserRepository,
            'scan_by_email_prefix',
            mock_scan
        ):
            response = authenticated_client.get("/api/users?q=alice")

            assert response.status_code == 200
            data = response.json()["data"]
            assert len(data) == 2
            assert data[0]["email"] == "alice@example.com"
            assert "hashed_password" not in data[0]

    def test_search_users_empty_query(self, authenticated_client):
        """Test search with empty query returns empty."""
        response = authenticated_client.get("/api/users?q=")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 0

    def test_search_users_no_query(self, authenticated_client):
        """Test search without query parameter returns empty."""
        response = authenticated_client.get("/api/users")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 0

    def test_search_users_with_limit(self, authenticated_client):
        """Test search respects limit parameter."""
        found_users = [
            UserInDB(
                id=f"user_{i}",
                email=f"user{i}@example.com",
                hashed_password="hashed",
                role="user",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

        async def mock_scan(self, query, limit, dynamodb):
            return found_users[:limit]

        from app.repositories import user_repository

        with patch.object(
            user_repository.UserRepository,
            'scan_by_email_prefix',
            mock_scan
        ):
            response = authenticated_client.get("/api/users?q=user&limit=3")

            assert response.status_code == 200
            data = response.json()["data"]
            assert len(data) == 3

    def test_search_users_unauthenticated(self, unauthenticated_client):
        """Test search requires authentication."""
        response = unauthenticated_client.get("/api/users?q=test")
        assert response.status_code == 403
