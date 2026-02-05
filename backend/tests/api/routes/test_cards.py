"""Card API endpoint tests - TDD RED phase."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.models.card import Card
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
def another_user():
    """Create another mock user for permission tests."""
    return User(
        id="user_456",
        email="another@example.com",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_card(mock_user: User):
    """Create sample card."""
    return Card(
        id="card_123",
        name="Test Card",
        code="print('Hello')",
        description="Test description",
        dataset_id="dataset_123",
        owner_id=mock_user.id,
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
    """Create test client with authentication."""

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


# ============================================================================
# GET /api/cards - List Cards
# ============================================================================


class TestListCards:
    """Tests for GET /api/cards."""

    def test_list_cards_authenticated(
        self, authenticated_client: TestClient, mock_user: User, sample_card: Card
    ) -> None:
        """Test listing cards for authenticated user."""
        from app.repositories import card_repository

        async def mock_list_func(self, owner_id, dynamodb):
            return [sample_card]

        with patch.object(
            card_repository.CardRepository, "list_by_owner", mock_list_func
        ):
            response = authenticated_client.get("/api/cards")

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "pagination" in response_data
        data = response_data["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == sample_card.id
        assert data[0]["owner_id"] == mock_user.id

    def test_list_cards_empty(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test listing cards when user has none."""
        from app.repositories import card_repository

        async def mock_list_func(self, owner_id, dynamodb):
            return []

        with patch.object(
            card_repository.CardRepository, "list_by_owner", mock_list_func
        ):
            response = authenticated_client.get("/api/cards")

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "pagination" in response_data
        data = response_data["data"]
        assert data == []


# ============================================================================
# POST /api/cards - Create Card
# ============================================================================


class TestCreateCard:
    """Tests for POST /api/cards."""

    def test_create_card_success(
        self, authenticated_client: TestClient, mock_user: User, sample_card: Card
    ) -> None:
        """Test creating card successfully."""
        from app.repositories import card_repository, dataset_repository

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            return MagicMock(id="dataset_123")

        async def mock_create_card(self, data, dynamodb):
            return sample_card

        with patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch.object(card_repository.CardRepository, "create", mock_create_card):
            response = authenticated_client.post(
                "/api/cards",
                json={
                    "name": "Test Card",
                    "code": "print('Hello')",
                    "dataset_id": "dataset_123",
                },
            )

        assert response.status_code == 201
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["id"] == sample_card.id
        assert data["name"] == sample_card.name

    def test_create_card_dataset_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test creating card with non-existent dataset_id."""
        from app.repositories import dataset_repository

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            return None

        with patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ):
            response = authenticated_client.post(
                "/api/cards",
                json={
                    "name": "Test Card",
                    "code": "print('Hello')",
                    "dataset_id": "nonexistent",
                },
            )

        assert response.status_code == 404
        assert "Dataset not found" in response.json()["detail"]

    def test_create_card_missing_code(self, authenticated_client: TestClient) -> None:
        """Test creating card without code field."""
        response = authenticated_client.post(
            "/api/cards",
            json={
                "name": "Test Card",
                "dataset_id": "dataset_123",
            },
        )

        assert response.status_code == 422

    def test_create_card_empty_code(self, authenticated_client: TestClient) -> None:
        """Test creating card with empty code."""
        response = authenticated_client.post(
            "/api/cards",
            json={
                "name": "Test Card",
                "code": "",
                "dataset_id": "dataset_123",
            },
        )

        assert response.status_code == 422


# ============================================================================
# GET /api/cards/{card_id} - Get Card Details
# ============================================================================


class TestGetCard:
    """Tests for GET /api/cards/{card_id}."""

    def test_get_card_success(
        self, authenticated_client: TestClient, sample_card: Card
    ) -> None:
        """Test getting card details."""
        from app.repositories import card_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        with patch.object(card_repository.CardRepository, "get_by_id", mock_get_by_id_card):
            response = authenticated_client.get(f"/api/cards/{sample_card.id}")

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["id"] == sample_card.id
        assert data["name"] == sample_card.name

    def test_get_card_not_found(self, authenticated_client: TestClient) -> None:
        """Test getting non-existent card."""
        from app.repositories import card_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return None

        with patch.object(card_repository.CardRepository, "get_by_id", mock_get_by_id_card):
            response = authenticated_client.get("/api/cards/nonexistent")

        assert response.status_code == 404


# ============================================================================
# PUT /api/cards/{card_id} - Update Card
# ============================================================================


class TestUpdateCard:
    """Tests for PUT /api/cards/{card_id}."""

    def test_update_card_success_as_owner(
        self, authenticated_client: TestClient, mock_user: User, sample_card: Card
    ) -> None:
        """Test updating card as owner."""
        from app.repositories import card_repository

        updated_card = Card(
            **{
                **sample_card.model_dump(),
                "name": "Updated Name",
            }
        )

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_update_card(self, pk, updates, dynamodb):
            return updated_card

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(card_repository.CardRepository, "update", mock_update_card):
            response = authenticated_client.put(
                f"/api/cards/{sample_card.id}",
                json={"name": "Updated Name"},
            )

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["name"] == "Updated Name"

    def test_update_card_forbidden_not_owner(
        self, authenticated_client: TestClient, another_user: User, sample_card: Card
    ) -> None:
        """Test updating card as non-owner (403)."""
        from app.repositories import card_repository

        other_user_card = Card(
            **{
                **sample_card.model_dump(),
                "owner_id": another_user.id,
            }
        )

        async def mock_get_by_id_card(self, pk, dynamodb):
            return other_user_card

        with patch.object(card_repository.CardRepository, "get_by_id", mock_get_by_id_card):
            response = authenticated_client.put(
                f"/api/cards/{sample_card.id}",
                json={"name": "Updated Name"},
            )

        assert response.status_code == 403

    def test_update_card_not_found(self, authenticated_client: TestClient) -> None:
        """Test updating non-existent card."""
        from app.repositories import card_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return None

        with patch.object(card_repository.CardRepository, "get_by_id", mock_get_by_id_card):
            response = authenticated_client.put(
                "/api/cards/nonexistent",
                json={"name": "Updated Name"},
            )

        assert response.status_code == 404


# ============================================================================
# DELETE /api/cards/{card_id} - Delete Card
# ============================================================================


class TestDeleteCard:
    """Tests for DELETE /api/cards/{card_id}."""

    def test_delete_card_success_as_owner(
        self, authenticated_client: TestClient, mock_user: User, sample_card: Card
    ) -> None:
        """Test deleting card as owner."""
        from app.repositories import card_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_delete_card(self, pk, dynamodb):
            pass

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(card_repository.CardRepository, "delete", mock_delete_card):
            response = authenticated_client.delete(f"/api/cards/{sample_card.id}")

        assert response.status_code == 204

    def test_delete_card_forbidden_not_owner(
        self, authenticated_client: TestClient, another_user: User, sample_card: Card
    ) -> None:
        """Test deleting card as non-owner (403)."""
        from app.repositories import card_repository

        other_user_card = Card(
            **{
                **sample_card.model_dump(),
                "owner_id": another_user.id,
            }
        )

        async def mock_get_by_id_card(self, pk, dynamodb):
            return other_user_card

        with patch.object(card_repository.CardRepository, "get_by_id", mock_get_by_id_card):
            response = authenticated_client.delete(f"/api/cards/{sample_card.id}")

        assert response.status_code == 403

    def test_delete_card_not_found(self, authenticated_client: TestClient) -> None:
        """Test deleting non-existent card."""
        from app.repositories import card_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return None

        with patch.object(card_repository.CardRepository, "get_by_id", mock_get_by_id_card):
            response = authenticated_client.delete("/api/cards/nonexistent")

        assert response.status_code == 404


# ============================================================================
# POST /api/cards/{card_id}/preview - Preview Card
# ============================================================================


class TestPreviewCard:
    """Tests for POST /api/cards/{card_id}/preview."""

    def test_preview_card_success(
        self, authenticated_client: TestClient, sample_card: Card
    ) -> None:
        """Test previewing card with filters."""
        from app.repositories import card_repository, dataset_repository
        from app.services.card_execution_service import CardExecutionResult

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            mock_dataset = MagicMock()
            mock_dataset.updated_at = datetime.now(timezone.utc)
            return mock_dataset

        async def mock_execute(self, *args, **kwargs):
            return CardExecutionResult(
                html="<div>Preview HTML</div>",
                used_columns=["col1"],
                filter_applicable=True,
                cached=False,
                execution_time_ms=100,
            )

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch(
            "app.services.card_execution_service.CardExecutionService.execute",
            mock_execute,
        ):
            response = authenticated_client.post(
                f"/api/cards/{sample_card.id}/preview",
                json={"filters": {"category": "A"}},
            )

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert "html" in data
        assert data["cached"] is False

    def test_preview_card_not_found(self, authenticated_client: TestClient) -> None:
        """Test previewing non-existent card."""
        from app.repositories import card_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return None

        with patch.object(card_repository.CardRepository, "get_by_id", mock_get_by_id_card):
            response = authenticated_client.post(
                "/api/cards/nonexistent/preview",
                json={"filters": {}},
            )

        assert response.status_code == 404

    def test_preview_card_executor_timeout(
        self, authenticated_client: TestClient, sample_card: Card
    ) -> None:
        """Test preview with Executor timeout."""
        from app.repositories import card_repository, dataset_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            mock_dataset = MagicMock()
            mock_dataset.updated_at = datetime.now(timezone.utc)
            return mock_dataset

        async def mock_execute(self, *args, **kwargs):
            raise RuntimeError("Executor timeout: Connection timeout")

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch(
            "app.services.card_execution_service.CardExecutionService.execute",
            mock_execute,
        ):
            response = authenticated_client.post(
                f"/api/cards/{sample_card.id}/preview",
                json={"filters": {}},
            )

        assert response.status_code == 500

    def test_preview_card_dataset_file_not_found_returns_404(
        self,
        authenticated_client: TestClient,
        mock_user: User,
        sample_card: Card,
        mock_dynamodb,
    ) -> None:
        """DatasetFileNotFoundError 発生時に HTTP 404 が返り監査ログが記録されること。"""
        from app.repositories import card_repository, dataset_repository
        from app.exceptions import DatasetFileNotFoundError

        s3_path = "s3://bucket/datasets/dataset_123/data.parquet"
        dataset_id = "dataset_123"

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            mock_dataset = MagicMock()
            mock_dataset.updated_at = datetime.now(timezone.utc)
            return mock_dataset

        async def mock_execute(self, *args, **kwargs):
            raise DatasetFileNotFoundError(s3_path=s3_path, dataset_id=dataset_id)

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch(
            "app.services.card_execution_service.CardExecutionService.execute",
            mock_execute,
        ), patch("app.api.routes.cards.AuditService") as MockAuditService:
            mock_audit_instance = MockAuditService.return_value
            mock_audit_instance.log_card_execution_failed = AsyncMock(return_value=None)

            response = authenticated_client.post(
                f"/api/cards/{sample_card.id}/preview",
                json={"filters": {}},
            )

        # Requirement 1: HTTP 404 status code
        assert response.status_code == 404

        # Requirement 2: Error message contains dataset file not found info
        response_body = response.json()
        assert "detail" in response_body
        assert "not found" in response_body["detail"].lower()
        assert s3_path in response_body["detail"] or dataset_id in response_body["detail"]

        # Requirement 3: Audit log is recorded with correct parameters
        mock_audit_instance.log_card_execution_failed.assert_called_once_with(
            user_id=mock_user.id,
            card_id=sample_card.id,
            error=str(DatasetFileNotFoundError(s3_path=s3_path, dataset_id=dataset_id)),
            dynamodb=mock_dynamodb,
        )

    def test_preview_card_failure_calls_audit_log(
        self,
        authenticated_client: TestClient,
        mock_user: User,
        sample_card: Card,
        mock_dynamodb,
    ) -> None:
        """Test that preview RuntimeError triggers audit log for card execution failure."""
        from app.repositories import card_repository, dataset_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            mock_dataset = MagicMock()
            mock_dataset.updated_at = datetime.now(timezone.utc)
            return mock_dataset

        async def mock_execute(self, *args, **kwargs):
            raise RuntimeError("Preview execution failed")

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch(
            "app.services.card_execution_service.CardExecutionService.execute",
            mock_execute,
        ), patch("app.api.routes.cards.AuditService") as MockAuditService:
            mock_audit_instance = MockAuditService.return_value
            mock_audit_instance.log_card_execution_failed = AsyncMock(return_value=None)

            response = authenticated_client.post(
                f"/api/cards/{sample_card.id}/preview",
                json={"filters": {}},
            )

        assert response.status_code == 500
        mock_audit_instance.log_card_execution_failed.assert_called_once_with(
            user_id=mock_user.id,
            card_id=sample_card.id,
            error=str(RuntimeError("Preview execution failed")),
            dynamodb=mock_dynamodb,
        )


# ============================================================================
# POST /api/cards/{card_id}/execute - Execute Card
# ============================================================================


class TestExecuteCard:
    """Tests for POST /api/cards/{card_id}/execute."""

    def test_execute_card_with_cache_hit(
        self, authenticated_client: TestClient, sample_card: Card
    ) -> None:
        """Test executing card with cache hit."""
        from app.repositories import card_repository, dataset_repository
        from app.services.card_execution_service import CardExecutionResult

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            mock_dataset = MagicMock()
            mock_dataset.updated_at = datetime.now(timezone.utc)
            return mock_dataset

        async def mock_execute(self, *args, **kwargs):
            return CardExecutionResult(
                html="<div>Cached HTML</div>",
                used_columns=["col1"],
                filter_applicable=True,
                cached=True,
                execution_time_ms=10,
            )

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch(
            "app.services.card_execution_service.CardExecutionService.execute",
            mock_execute,
        ):
            response = authenticated_client.post(
                f"/api/cards/{sample_card.id}/execute",
                json={"filters": {"category": "A"}, "use_cache": True},
            )

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["cached"] is True
        assert "html" in data

    def test_execute_card_cache_miss(
        self, authenticated_client: TestClient, sample_card: Card
    ) -> None:
        """Test executing card with cache miss."""
        from app.repositories import card_repository, dataset_repository
        from app.services.card_execution_service import CardExecutionResult

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            mock_dataset = MagicMock()
            mock_dataset.updated_at = datetime.now(timezone.utc)
            return mock_dataset

        async def mock_execute(self, *args, **kwargs):
            return CardExecutionResult(
                html="<div>Fresh HTML</div>",
                used_columns=["col1"],
                filter_applicable=True,
                cached=False,
                execution_time_ms=150,
            )

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch(
            "app.services.card_execution_service.CardExecutionService.execute",
            mock_execute,
        ):
            response = authenticated_client.post(
                f"/api/cards/{sample_card.id}/execute",
                json={"filters": {}, "use_cache": True},
            )

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["cached"] is False

    def test_execute_card_use_cache_false(
        self, authenticated_client: TestClient, sample_card: Card
    ) -> None:
        """Test executing card with use_cache=False."""
        from app.repositories import card_repository, dataset_repository
        from app.services.card_execution_service import CardExecutionResult

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            mock_dataset = MagicMock()
            mock_dataset.updated_at = datetime.now(timezone.utc)
            return mock_dataset

        async def mock_execute(self, *args, **kwargs):
            # Verify use_cache=False was passed
            assert kwargs.get("use_cache") is False
            return CardExecutionResult(
                html="<div>No Cache HTML</div>",
                used_columns=["col1"],
                filter_applicable=False,
                cached=False,
                execution_time_ms=200,
            )

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch(
            "app.services.card_execution_service.CardExecutionService.execute",
            mock_execute,
        ):
            response = authenticated_client.post(
                f"/api/cards/{sample_card.id}/execute",
                json={"filters": {}, "use_cache": False},
            )

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["cached"] is False

    def test_execute_card_failure_calls_audit_log(
        self,
        authenticated_client: TestClient,
        mock_user: User,
        sample_card: Card,
        mock_dynamodb,
    ) -> None:
        """Test that execute RuntimeError triggers audit log for card execution failure."""
        from app.repositories import card_repository, dataset_repository

        async def mock_get_by_id_card(self, pk, dynamodb):
            return sample_card

        async def mock_get_by_id_dataset(self, pk, dynamodb):
            mock_dataset = MagicMock()
            mock_dataset.updated_at = datetime.now(timezone.utc)
            return mock_dataset

        async def mock_execute(self, *args, **kwargs):
            raise RuntimeError("Execution failed")

        with patch.object(
            card_repository.CardRepository, "get_by_id", mock_get_by_id_card
        ), patch.object(
            dataset_repository.DatasetRepository, "get_by_id", mock_get_by_id_dataset
        ), patch(
            "app.services.card_execution_service.CardExecutionService.execute",
            mock_execute,
        ), patch("app.api.routes.cards.AuditService") as MockAuditService:
            mock_audit_instance = MockAuditService.return_value
            mock_audit_instance.log_card_execution_failed = AsyncMock(return_value=None)

            response = authenticated_client.post(
                f"/api/cards/{sample_card.id}/execute",
                json={"filters": {}, "use_cache": True},
            )

        assert response.status_code == 500
        mock_audit_instance.log_card_execution_failed.assert_called_once_with(
            user_id=mock_user.id,
            card_id=sample_card.id,
            error=str(RuntimeError("Execution failed")),
            dynamodb=mock_dynamodb,
        )
