"""Tests for S3 Import API routes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.models.user import User


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    return User(
        id="user_test123",
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


class TestS3ImportEndpoint:
    """Tests for POST /api/datasets/s3-import."""

    def test_s3_import_success(self, authenticated_client):
        """Test successful S3 import returns 201."""
        mock_dataset = MagicMock()
        mock_dataset.model_dump.return_value = {
            "id": "ds_test123",
            "name": "test-dataset",
            "source_type": "s3_csv",
        }

        with patch("app.api.routes.datasets.DatasetService") as MockService:
            instance = MockService.return_value
            instance.import_s3_csv = AsyncMock(return_value=mock_dataset)

            response = authenticated_client.post(
                "/api/datasets/s3-import",
                json={
                    "name": "test-dataset",
                    "s3_bucket": "my-bucket",
                    "s3_key": "data/file.csv",
                },
            )

        assert response.status_code == 201
        response_data = response.json()
        assert "data" in response_data
        assert response_data["data"]["name"] == "test-dataset"

    def test_s3_import_validation_error(self, authenticated_client):
        """Test S3 import with ValueError returns 422."""
        with patch("app.api.routes.datasets.DatasetService") as MockService:
            instance = MockService.return_value
            instance.import_s3_csv = AsyncMock(
                side_effect=ValueError("S3 object not found")
            )

            response = authenticated_client.post(
                "/api/datasets/s3-import",
                json={
                    "name": "test-dataset",
                    "s3_bucket": "my-bucket",
                    "s3_key": "nonexistent.csv",
                },
            )

        assert response.status_code == 422

    def test_s3_import_missing_fields(self, authenticated_client):
        """Test S3 import with missing required fields returns 422."""
        response = authenticated_client.post(
            "/api/datasets/s3-import",
            json={"name": "test"},
        )
        assert response.status_code == 422

    def test_s3_import_unauthenticated(self, unauthenticated_client):
        """Test S3 import without auth returns 403."""
        response = unauthenticated_client.post(
            "/api/datasets/s3-import",
            json={
                "name": "test",
                "s3_bucket": "bucket",
                "s3_key": "key.csv",
            },
        )
        assert response.status_code == 403

    def test_s3_import_with_all_options(self, authenticated_client):
        """Test S3 import with all optional fields."""
        mock_dataset = MagicMock()
        mock_dataset.model_dump.return_value = {
            "id": "ds_test456",
            "name": "full-options-dataset",
            "source_type": "s3_csv",
        }

        with patch("app.api.routes.datasets.DatasetService") as MockService:
            instance = MockService.return_value
            instance.import_s3_csv = AsyncMock(return_value=mock_dataset)

            response = authenticated_client.post(
                "/api/datasets/s3-import",
                json={
                    "name": "full-options-dataset",
                    "s3_bucket": "my-bucket",
                    "s3_key": "data/file.csv",
                    "has_header": False,
                    "encoding": "shift_jis",
                    "delimiter": "\t",
                    "partition_column": "region",
                },
            )

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["data"]["name"] == "full-options-dataset"

        # Verify the service was called with correct parameters
        instance.import_s3_csv.assert_called_once()
        call_kwargs = instance.import_s3_csv.call_args[1]
        assert call_kwargs["has_header"] is False
        assert call_kwargs["encoding"] == "shift_jis"
        assert call_kwargs["delimiter"] == "\t"
        assert call_kwargs["partition_column"] == "region"

    def test_s3_import_empty_name(self, authenticated_client):
        """Test S3 import with empty name returns 422."""
        response = authenticated_client.post(
            "/api/datasets/s3-import",
            json={
                "name": "",
                "s3_bucket": "my-bucket",
                "s3_key": "data/file.csv",
            },
        )
        assert response.status_code == 422

    def test_s3_import_empty_bucket(self, authenticated_client):
        """Test S3 import with empty bucket returns 422."""
        response = authenticated_client.post(
            "/api/datasets/s3-import",
            json={
                "name": "test",
                "s3_bucket": "",
                "s3_key": "data/file.csv",
            },
        )
        assert response.status_code == 422

    def test_s3_import_empty_key(self, authenticated_client):
        """Test S3 import with empty key returns 422."""
        response = authenticated_client.post(
            "/api/datasets/s3-import",
            json={
                "name": "test",
                "s3_bucket": "my-bucket",
                "s3_key": "",
            },
        )
        assert response.status_code == 422
