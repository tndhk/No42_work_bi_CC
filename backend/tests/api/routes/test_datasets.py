"""Dataset API endpoint tests."""
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.models.dataset import Dataset, ColumnSchema
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
def sample_dataset():
    """Create sample dataset."""
    return Dataset(
        id="ds_abc123456789",
        name="Test Dataset",
        description="Test description",
        source_type="csv",
        row_count=100,
        schema=[
            ColumnSchema(name="id", data_type="int64", nullable=False),
            ColumnSchema(name="name", data_type="string", nullable=False),
        ],
        owner_id="user_123",
        s3_path="datasets/ds_abc123456789/data/part-0000.parquet",
        column_count=2,
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
    """Create test client with authentication and dependency overrides.

    Uses FastAPI's dependency_overrides to bypass real JWT decoding
    and DynamoDB/S3 connections, matching the pattern from conftest.py.
    """

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


class TestListDatasets:
    """Tests for GET /api/datasets."""

    def test_list_datasets_authenticated(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test listing datasets for authenticated user."""
        async def mock_list_func(self, owner_id, dynamodb):
            return [sample_dataset]

        from app.repositories import dataset_repository

        with patch.object(dataset_repository.DatasetRepository, 'list_by_owner', new=mock_list_func):
            response = authenticated_client.get("/api/datasets")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == "ds_abc123456789"
            assert data[0]["name"] == "Test Dataset"

    def test_list_datasets_unauthenticated(self, unauthenticated_client: TestClient) -> None:
        """Test listing datasets without authentication."""
        response = unauthenticated_client.get("/api/datasets")
        assert response.status_code == 403


class TestCreateDataset:
    """Tests for POST /api/datasets."""

    def test_create_dataset_success(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test successful dataset creation with multipart upload."""
        csv_content = b"id,name\n1,Alice\n2,Bob\n"

        with patch('app.services.dataset_service.DatasetService.import_csv') as mock_import:
            mock_import.return_value = sample_dataset

            response = authenticated_client.post(
                "/api/datasets",
                files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
                data={"name": "Test Dataset", "description": "Test description"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["id"] == "ds_abc123456789"
            assert data["name"] == "Test Dataset"
            mock_import.assert_called_once()

    def test_create_dataset_no_file(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test dataset creation without file."""
        response = authenticated_client.post(
            "/api/datasets",
            data={"name": "Test Dataset"},
        )

        assert response.status_code == 422

    def test_create_dataset_empty_name(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test dataset creation with empty name."""
        csv_content = b"id,name\n1,Alice\n"

        response = authenticated_client.post(
            "/api/datasets",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            data={"name": ""},
        )

        assert response.status_code == 422

    def test_create_dataset_unauthenticated(self, unauthenticated_client: TestClient) -> None:
        """Test dataset creation without authentication."""
        csv_content = b"id,name\n1,Alice\n"

        response = unauthenticated_client.post(
            "/api/datasets",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            data={"name": "Test Dataset"},
        )

        assert response.status_code == 403


class TestGetDataset:
    """Tests for GET /api/datasets/{dataset_id}."""

    def test_get_dataset_success(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test retrieving dataset by ID."""
        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = sample_dataset

            response = authenticated_client.get(
                f"/api/datasets/{sample_dataset.id}",
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == sample_dataset.id
            assert data["name"] == sample_dataset.name

    def test_get_dataset_not_found(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test retrieving non-existent dataset."""
        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = None

            response = authenticated_client.get(
                "/api/datasets/nonexistent",
            )

            assert response.status_code == 404

    def test_get_dataset_unauthenticated(self, unauthenticated_client: TestClient) -> None:
        """Test retrieving dataset without authentication."""
        response = unauthenticated_client.get("/api/datasets/ds_abc123456789")
        assert response.status_code == 403


class TestUpdateDataset:
    """Tests for PUT /api/datasets/{dataset_id}."""

    def test_update_dataset_success(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test updating dataset by owner."""
        updated_dataset = Dataset(
            **{
                **sample_dataset.model_dump(by_alias=True),
                'name': 'Updated Name',
                'description': 'Updated description',
            }
        )

        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get, \
             patch('app.repositories.dataset_repository.DatasetRepository.update') as mock_update:
            mock_get.return_value = sample_dataset
            mock_update.return_value = updated_dataset

            response = authenticated_client.put(
                f"/api/datasets/{sample_dataset.id}",
                json={
                    "name": "Updated Name",
                    "description": "Updated description",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
            assert data["description"] == "Updated description"

    def test_update_dataset_forbidden(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test updating dataset by non-owner."""
        other_user_dataset = Dataset(
            **{**sample_dataset.model_dump(by_alias=True), 'owner_id': 'other_user'}
        )

        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = other_user_dataset

            response = authenticated_client.put(
                f"/api/datasets/{sample_dataset.id}",
                json={"name": "Updated Name"},
            )

            assert response.status_code == 403

    def test_update_dataset_not_found(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test updating non-existent dataset."""
        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = None

            response = authenticated_client.put(
                "/api/datasets/nonexistent",
                json={"name": "Updated Name"},
            )

            assert response.status_code == 404


class TestDeleteDataset:
    """Tests for DELETE /api/datasets/{dataset_id}."""

    def test_delete_dataset_success(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test deleting dataset by owner."""
        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get, \
             patch('app.repositories.dataset_repository.DatasetRepository.delete') as mock_delete:
            mock_get.return_value = sample_dataset
            mock_delete.return_value = None

            response = authenticated_client.delete(
                f"/api/datasets/{sample_dataset.id}",
            )

            assert response.status_code == 204
            mock_delete.assert_called_once()

    def test_delete_dataset_forbidden(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test deleting dataset by non-owner."""
        other_user_dataset = Dataset(
            **{**sample_dataset.model_dump(by_alias=True), 'owner_id': 'other_user'}
        )

        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = other_user_dataset

            response = authenticated_client.delete(
                f"/api/datasets/{sample_dataset.id}",
            )

            assert response.status_code == 403

    def test_delete_dataset_not_found(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test deleting non-existent dataset."""
        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = None

            response = authenticated_client.delete(
                "/api/datasets/nonexistent",
            )

            assert response.status_code == 404


class TestGetDatasetPreview:
    """Tests for GET /api/datasets/{dataset_id}/preview."""

    def test_get_preview_success(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test getting dataset preview."""
        preview_data = {
            'columns': ['id', 'name'],
            'rows': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}],
            'total_rows': 100,
            'preview_rows': 2,
        }

        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get, \
             patch('app.services.dataset_service.DatasetService.get_preview') as mock_preview:
            mock_get.return_value = sample_dataset
            mock_preview.return_value = preview_data

            response = authenticated_client.get(
                f"/api/datasets/{sample_dataset.id}/preview",
            )

            assert response.status_code == 200
            data = response.json()
            assert data['columns'] == ['id', 'name']
            assert len(data['rows']) == 2
            assert data['total_rows'] == 100

    def test_get_preview_with_max_rows(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test getting dataset preview with custom max_rows."""
        preview_data = {
            'columns': ['id', 'name'],
            'rows': [{'id': i, 'name': f'User{i}'} for i in range(50)],
            'total_rows': 100,
            'preview_rows': 50,
        }

        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get, \
             patch('app.services.dataset_service.DatasetService.get_preview') as mock_preview:
            mock_get.return_value = sample_dataset
            mock_preview.return_value = preview_data

            response = authenticated_client.get(
                f"/api/datasets/{sample_dataset.id}/preview?max_rows=50",
            )

            assert response.status_code == 200
            data = response.json()
            assert data['preview_rows'] == 50

    def test_get_preview_invalid_max_rows_too_small(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test preview with max_rows < 1."""
        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = sample_dataset

            response = authenticated_client.get(
                f"/api/datasets/{sample_dataset.id}/preview?max_rows=0",
            )

            assert response.status_code == 422

    def test_get_preview_invalid_max_rows_too_large(
        self, authenticated_client: TestClient, mock_user: User, sample_dataset: Dataset
    ) -> None:
        """Test preview with max_rows > 1000."""
        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = sample_dataset

            response = authenticated_client.get(
                f"/api/datasets/{sample_dataset.id}/preview?max_rows=2000",
            )

            assert response.status_code == 422

    def test_get_preview_dataset_not_found(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test preview for non-existent dataset."""
        with patch('app.repositories.dataset_repository.DatasetRepository.get_by_id') as mock_get:
            mock_get.return_value = None

            response = authenticated_client.get(
                "/api/datasets/nonexistent/preview",
            )

            assert response.status_code == 404
