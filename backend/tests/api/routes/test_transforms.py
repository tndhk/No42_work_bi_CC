"""Transform API endpoint tests - TDD RED phase."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.models.transform import Transform
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
def sample_transform(mock_user: User):
    """Create sample transform."""
    return Transform(
        id="transform_123",
        name="Test Transform",
        owner_id=mock_user.id,
        input_dataset_ids=["dataset_001", "dataset_002"],
        output_dataset_id="dataset_out_001",
        code="df = df1.merge(df2, on='id')",
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
# GET /api/transforms - List Transforms
# ============================================================================


class TestListTransforms:
    """Tests for GET /api/transforms."""

    def test_list_transforms_authenticated(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test listing transforms for authenticated user."""
        from app.repositories import transform_repository

        async def mock_list_func(self, owner_id, dynamodb):
            return [sample_transform]

        with patch.object(
            transform_repository.TransformRepository, "list_by_owner", mock_list_func
        ):
            response = authenticated_client.get("/api/transforms")

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "pagination" in response_data
        data = response_data["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == sample_transform.id
        assert data[0]["owner_id"] == mock_user.id

    def test_list_transforms_empty(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test listing transforms when user has none."""
        from app.repositories import transform_repository

        async def mock_list_func(self, owner_id, dynamodb):
            return []

        with patch.object(
            transform_repository.TransformRepository, "list_by_owner", mock_list_func
        ):
            response = authenticated_client.get("/api/transforms")

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "pagination" in response_data
        data = response_data["data"]
        assert data == []

    def test_list_transforms_pagination(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test listing transforms with pagination parameters."""
        from app.repositories import transform_repository

        transforms = [
            Transform(
                id=f"transform_{i}",
                name=f"Transform {i}",
                owner_id=mock_user.id,
                input_dataset_ids=["dataset_001"],
                code="df = df1",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

        async def mock_list_func(self, owner_id, dynamodb):
            return transforms

        with patch.object(
            transform_repository.TransformRepository, "list_by_owner", mock_list_func
        ):
            response = authenticated_client.get("/api/transforms?limit=2&offset=1")

        assert response.status_code == 200
        response_data = response.json()
        assert "pagination" in response_data
        pagination = response_data["pagination"]
        assert pagination["total"] == 5
        assert pagination["limit"] == 2
        assert pagination["offset"] == 1
        assert pagination["has_next"] is True
        assert len(response_data["data"]) == 2


# ============================================================================
# POST /api/transforms - Create Transform
# ============================================================================


class TestCreateTransform:
    """Tests for POST /api/transforms."""

    def test_create_transform_success(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test creating transform successfully."""
        from app.repositories import transform_repository

        async def mock_create_transform(self, data, dynamodb):
            return sample_transform

        with patch.object(
            transform_repository.TransformRepository, "create", mock_create_transform
        ):
            response = authenticated_client.post(
                "/api/transforms",
                json={
                    "name": "Test Transform",
                    "input_dataset_ids": ["dataset_001", "dataset_002"],
                    "code": "df = df1.merge(df2, on='id')",
                },
            )

        assert response.status_code == 201
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["id"] == sample_transform.id
        assert data["name"] == sample_transform.name
        assert data["owner_id"] == mock_user.id

    def test_create_transform_missing_name(
        self, authenticated_client: TestClient
    ) -> None:
        """Test creating transform without name field."""
        response = authenticated_client.post(
            "/api/transforms",
            json={
                "input_dataset_ids": ["dataset_001"],
                "code": "df = df1",
            },
        )

        assert response.status_code == 422

    def test_create_transform_empty_name(
        self, authenticated_client: TestClient
    ) -> None:
        """Test creating transform with empty name."""
        response = authenticated_client.post(
            "/api/transforms",
            json={
                "name": "",
                "input_dataset_ids": ["dataset_001"],
                "code": "df = df1",
            },
        )

        assert response.status_code == 422

    def test_create_transform_missing_input_dataset_ids(
        self, authenticated_client: TestClient
    ) -> None:
        """Test creating transform without input_dataset_ids."""
        response = authenticated_client.post(
            "/api/transforms",
            json={
                "name": "Test Transform",
                "code": "df = df1",
            },
        )

        assert response.status_code == 422

    def test_create_transform_empty_input_dataset_ids(
        self, authenticated_client: TestClient
    ) -> None:
        """Test creating transform with empty input_dataset_ids."""
        response = authenticated_client.post(
            "/api/transforms",
            json={
                "name": "Test Transform",
                "input_dataset_ids": [],
                "code": "df = df1",
            },
        )

        assert response.status_code == 422

    def test_create_transform_missing_code(
        self, authenticated_client: TestClient
    ) -> None:
        """Test creating transform without code field."""
        response = authenticated_client.post(
            "/api/transforms",
            json={
                "name": "Test Transform",
                "input_dataset_ids": ["dataset_001"],
            },
        )

        assert response.status_code == 422

    def test_create_transform_empty_code(
        self, authenticated_client: TestClient
    ) -> None:
        """Test creating transform with empty code."""
        response = authenticated_client.post(
            "/api/transforms",
            json={
                "name": "Test Transform",
                "input_dataset_ids": ["dataset_001"],
                "code": "",
            },
        )

        assert response.status_code == 422


# ============================================================================
# GET /api/transforms/{transform_id} - Get Transform Details
# ============================================================================


class TestGetTransform:
    """Tests for GET /api/transforms/{transform_id}."""

    def test_get_transform_success(
        self, authenticated_client: TestClient, sample_transform: Transform
    ) -> None:
        """Test getting transform details."""
        from app.repositories import transform_repository

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return sample_transform

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ):
            response = authenticated_client.get(f"/api/transforms/{sample_transform.id}")

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["id"] == sample_transform.id
        assert data["name"] == sample_transform.name
        assert data["input_dataset_ids"] == sample_transform.input_dataset_ids
        assert data["code"] == sample_transform.code

    def test_get_transform_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test getting non-existent transform."""
        from app.repositories import transform_repository

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return None

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ):
            response = authenticated_client.get("/api/transforms/nonexistent")

        assert response.status_code == 404
        assert "Transform not found" in response.json()["detail"]


# ============================================================================
# PUT /api/transforms/{transform_id} - Update Transform
# ============================================================================


class TestUpdateTransform:
    """Tests for PUT /api/transforms/{transform_id}."""

    def test_update_transform_success_as_owner(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test updating transform as owner."""
        from app.repositories import transform_repository

        updated_transform = Transform(
            **{
                **sample_transform.model_dump(),
                "name": "Updated Transform Name",
            }
        )

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return sample_transform

        async def mock_update_transform(self, pk, updates, dynamodb):
            return updated_transform

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ), patch.object(
            transform_repository.TransformRepository, "update", mock_update_transform
        ):
            response = authenticated_client.put(
                f"/api/transforms/{sample_transform.id}",
                json={"name": "Updated Transform Name"},
            )

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["name"] == "Updated Transform Name"

    def test_update_transform_forbidden_not_owner(
        self, authenticated_client: TestClient, another_user: User, sample_transform: Transform
    ) -> None:
        """Test updating transform as non-owner (403)."""
        from app.repositories import transform_repository

        other_user_transform = Transform(
            **{
                **sample_transform.model_dump(),
                "owner_id": another_user.id,
            }
        )

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return other_user_transform

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ):
            response = authenticated_client.put(
                f"/api/transforms/{sample_transform.id}",
                json={"name": "Updated Transform Name"},
            )

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_update_transform_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test updating non-existent transform."""
        from app.repositories import transform_repository

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return None

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ):
            response = authenticated_client.put(
                "/api/transforms/nonexistent",
                json={"name": "Updated Transform Name"},
            )

        assert response.status_code == 404
        assert "Transform not found" in response.json()["detail"]

    def test_update_transform_partial_update(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test updating only some fields of transform."""
        from app.repositories import transform_repository

        updated_transform = Transform(
            **{
                **sample_transform.model_dump(),
                "code": "df = df1.join(df2)",
            }
        )

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return sample_transform

        async def mock_update_transform(self, pk, updates, dynamodb):
            return updated_transform

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ), patch.object(
            transform_repository.TransformRepository, "update", mock_update_transform
        ):
            response = authenticated_client.put(
                f"/api/transforms/{sample_transform.id}",
                json={"code": "df = df1.join(df2)"},
            )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["code"] == "df = df1.join(df2)"


# ============================================================================
# DELETE /api/transforms/{transform_id} - Delete Transform
# ============================================================================


class TestDeleteTransform:
    """Tests for DELETE /api/transforms/{transform_id}."""

    def test_delete_transform_success_as_owner(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test deleting transform as owner."""
        from app.repositories import transform_repository

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return sample_transform

        async def mock_delete_transform(self, pk, dynamodb):
            pass

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ), patch.object(
            transform_repository.TransformRepository, "delete", mock_delete_transform
        ):
            response = authenticated_client.delete(f"/api/transforms/{sample_transform.id}")

        assert response.status_code == 204

    def test_delete_transform_forbidden_not_owner(
        self, authenticated_client: TestClient, another_user: User, sample_transform: Transform
    ) -> None:
        """Test deleting transform as non-owner (403)."""
        from app.repositories import transform_repository

        other_user_transform = Transform(
            **{
                **sample_transform.model_dump(),
                "owner_id": another_user.id,
            }
        )

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return other_user_transform

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ):
            response = authenticated_client.delete(f"/api/transforms/{sample_transform.id}")

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_delete_transform_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test deleting non-existent transform."""
        from app.repositories import transform_repository

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return None

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ):
            response = authenticated_client.delete("/api/transforms/nonexistent")

        assert response.status_code == 404
        assert "Transform not found" in response.json()["detail"]


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.fixture
def unauthenticated_client():
    """Create test client without authentication."""
    return TestClient(app)


class TestTransformAuthentication:
    """Tests for authentication requirements."""

    def test_list_transforms_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test listing transforms without authentication."""
        response = unauthenticated_client.get("/api/transforms")
        assert response.status_code == 403

    def test_create_transform_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test creating transform without authentication."""
        response = unauthenticated_client.post(
            "/api/transforms",
            json={
                "name": "Test Transform",
                "input_dataset_ids": ["dataset_001"],
                "code": "df = df1",
            },
        )
        assert response.status_code == 403

    def test_get_transform_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test getting transform without authentication."""
        response = unauthenticated_client.get("/api/transforms/transform_123")
        assert response.status_code == 403

    def test_update_transform_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test updating transform without authentication."""
        response = unauthenticated_client.put(
            "/api/transforms/transform_123",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 403

    def test_delete_transform_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test deleting transform without authentication."""
        response = unauthenticated_client.delete("/api/transforms/transform_123")
        assert response.status_code == 403

    def test_execute_transform_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test executing transform without authentication."""
        response = unauthenticated_client.post("/api/transforms/transform_123/execute")
        assert response.status_code == 403


# ============================================================================
# POST /api/transforms/{transform_id}/execute - Execute Transform
# ============================================================================


class TestExecuteTransform:
    """Tests for POST /api/transforms/{transform_id}/execute."""

    def test_execute_transform_success_as_owner(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test executing transform as owner."""
        from app.repositories import transform_repository
        from app.services import transform_execution_service

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return sample_transform

        mock_result = transform_execution_service.TransformExecutionResult(
            execution_id="exec_123",
            output_dataset_id="dataset_output_123",
            row_count=100,
            column_names=["col1", "col2"],
            execution_time_ms=150.0,
        )

        async def mock_execute(self, transform, dynamodb, s3):
            return mock_result

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ), patch.object(
            transform_execution_service.TransformExecutionService, "execute", mock_execute
        ):
            response = authenticated_client.post(f"/api/transforms/{sample_transform.id}/execute")

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        data = response_data["data"]
        assert data["execution_id"] == "exec_123"
        assert data["output_dataset_id"] == "dataset_output_123"
        assert data["row_count"] == 100
        assert data["column_names"] == ["col1", "col2"]
        assert data["execution_time_ms"] == 150.0

    def test_execute_transform_forbidden_not_owner(
        self, authenticated_client: TestClient, another_user: User, sample_transform: Transform
    ) -> None:
        """Test executing transform as non-owner (403)."""
        from app.repositories import transform_repository

        other_user_transform = Transform(
            **{
                **sample_transform.model_dump(),
                "owner_id": another_user.id,
            }
        )

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return other_user_transform

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ):
            response = authenticated_client.post(f"/api/transforms/{sample_transform.id}/execute")

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_execute_transform_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test executing non-existent transform."""
        from app.repositories import transform_repository

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return None

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ):
            response = authenticated_client.post("/api/transforms/nonexistent/execute")

        assert response.status_code == 404
        assert "Transform not found" in response.json()["detail"]

    def test_execute_transform_input_dataset_not_found(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test executing transform when input dataset not found."""
        from app.repositories import transform_repository
        from app.services import transform_execution_service

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return sample_transform

        async def mock_execute(self, transform, dynamodb, s3):
            raise ValueError("Input dataset 'dataset_001' not found")

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ), patch.object(
            transform_execution_service.TransformExecutionService, "execute", mock_execute
        ):
            response = authenticated_client.post(f"/api/transforms/{sample_transform.id}/execute")

        assert response.status_code == 400
        assert "Input dataset" in response.json()["detail"]

    def test_execute_transform_executor_error(
        self, authenticated_client: TestClient, mock_user: User, sample_transform: Transform
    ) -> None:
        """Test executing transform when executor fails."""
        from app.repositories import transform_repository
        from app.services import transform_execution_service

        async def mock_get_by_id_transform(self, pk, dynamodb):
            return sample_transform

        async def mock_execute(self, transform, dynamodb, s3):
            raise RuntimeError("Executor failed after 3 attempts")

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id_transform
        ), patch.object(
            transform_execution_service.TransformExecutionService, "execute", mock_execute
        ):
            response = authenticated_client.post(f"/api/transforms/{sample_transform.id}/execute")

        assert response.status_code == 500
        assert "Executor failed" in response.json()["detail"]


# ============================================================================
# GET /api/transforms/{transform_id}/executions - List Transform Executions
# ============================================================================


class TestListTransformExecutions:
    """Tests for GET /api/transforms/{transform_id}/executions."""

    def test_list_executions_success(
        self, authenticated_client, mock_user, sample_transform
    ):
        """Test listing executions for a transform."""
        from app.repositories import transform_repository
        from app.repositories.transform_execution_repository import TransformExecutionRepository
        from app.models.transform_execution import TransformExecution
        from datetime import datetime, timezone

        async def mock_get_by_id(self, pk, dynamodb):
            return sample_transform

        mock_execution = TransformExecution(
            execution_id="exec-001",
            transform_id=sample_transform.id,
            status="success",
            started_at=datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 2, 4, 10, 0, 5, tzinfo=timezone.utc),
            duration_ms=5000.0,
            output_row_count=100,
            output_dataset_id="ds-out-001",
            triggered_by="manual",
        )

        async def mock_list_by_transform(self, transform_id, dynamodb, limit=20):
            return [mock_execution]

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id
        ), patch.object(
            TransformExecutionRepository, "list_by_transform", mock_list_by_transform
        ):
            response = authenticated_client.get(
                f"/api/transforms/{sample_transform.id}/executions"
            )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["execution_id"] == "exec-001"
        assert data["data"][0]["status"] == "success"

    def test_list_executions_empty(
        self, authenticated_client, mock_user, sample_transform
    ):
        """Test listing executions when none exist."""
        from app.repositories import transform_repository
        from app.repositories.transform_execution_repository import TransformExecutionRepository

        async def mock_get_by_id(self, pk, dynamodb):
            return sample_transform

        async def mock_list_by_transform(self, transform_id, dynamodb, limit=20):
            return []

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id
        ), patch.object(
            TransformExecutionRepository, "list_by_transform", mock_list_by_transform
        ):
            response = authenticated_client.get(
                f"/api/transforms/{sample_transform.id}/executions"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_list_executions_transform_not_found(
        self, authenticated_client
    ):
        """Test listing executions for non-existent transform."""
        from app.repositories import transform_repository

        async def mock_get_by_id(self, pk, dynamodb):
            return None

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id
        ):
            response = authenticated_client.get(
                "/api/transforms/nonexistent/executions"
            )

        assert response.status_code == 404

    def test_list_executions_pagination(
        self, authenticated_client, mock_user, sample_transform
    ):
        """Test listing executions with pagination."""
        from app.repositories import transform_repository
        from app.repositories.transform_execution_repository import TransformExecutionRepository
        from app.models.transform_execution import TransformExecution
        from datetime import datetime, timezone

        async def mock_get_by_id(self, pk, dynamodb):
            return sample_transform

        executions = [
            TransformExecution(
                execution_id=f"exec-{i:03d}",
                transform_id=sample_transform.id,
                status="success",
                started_at=datetime(2026, 2, 4, 10 + i, 0, 0, tzinfo=timezone.utc),
                triggered_by="manual",
            )
            for i in range(5)
        ]

        async def mock_list_by_transform(self, transform_id, dynamodb, limit=20):
            return executions[:limit]

        with patch.object(
            transform_repository.TransformRepository, "get_by_id", mock_get_by_id
        ), patch.object(
            TransformExecutionRepository, "list_by_transform", mock_list_by_transform
        ):
            response = authenticated_client.get(
                f"/api/transforms/{sample_transform.id}/executions?limit=2&offset=1"
            )

        assert response.status_code == 200
        data = response.json()
        assert "pagination" in data

    def test_list_executions_unauthenticated(self):
        """Test listing executions without authentication."""
        client = TestClient(app)
        response = client.get("/api/transforms/transform_123/executions")
        assert response.status_code == 403
