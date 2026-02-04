"""Dashboard API endpoint tests."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource
from app.models.dashboard import Dashboard, LayoutItem, FilterDefinition
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
def mock_other_user():
    """Create mock other user for ownership tests."""
    return User(
        id="user_456",
        email="other@example.com",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_layout():
    """Create sample layout items."""
    return [
        LayoutItem(card_id="card_1", x=0, y=0, w=4, h=3),
        LayoutItem(card_id="card_2", x=4, y=0, w=4, h=3),
    ]


@pytest.fixture
def sample_filters():
    """Create sample filter definitions."""
    return [
        FilterDefinition(
            id="filter_1",
            type="select",
            column="category",
            label="Category",
            multi_select=True,
        ),
    ]


@pytest.fixture
def sample_dashboard(sample_layout, sample_filters):
    """Create sample dashboard."""
    return Dashboard(
        id="dash_123",
        name="Test Dashboard",
        description="Test description",
        layout=sample_layout,
        filters=sample_filters,
        owner_id="user_123",
        default_filter_view_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_dashboard_no_layout():
    """Create sample dashboard without layout."""
    return Dashboard(
        id="dash_456",
        name="Empty Dashboard",
        description="No layout",
        layout=None,
        filters=None,
        owner_id="user_123",
        default_filter_view_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_dashboard_other_owner(sample_layout):
    """Create sample dashboard owned by different user."""
    return Dashboard(
        id="dash_789",
        name="Other User Dashboard",
        description="Owned by other",
        layout=sample_layout,
        filters=None,
        owner_id="user_456",
        default_filter_view_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_dynamodb():
    """Create mock DynamoDB resource."""
    return MagicMock()


@pytest.fixture
def authenticated_client(mock_user, mock_dynamodb):
    """Create test client with authentication and dependency overrides."""

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
    """Create test client without authentication overrides."""
    return TestClient(app)


class TestListDashboards:
    """Tests for GET /api/dashboards."""

    def test_list_dashboards_authenticated(
        self, authenticated_client: TestClient, mock_user: User, sample_dashboard: Dashboard
    ) -> None:
        """Test listing dashboards for authenticated user."""
        async def mock_list_func(self, owner_id, dynamodb):
            return [sample_dashboard]

        async def mock_list_by_target(self, shared_to_id, dynamodb):
            return []

        async def mock_list_groups(self, user_id, dynamodb):
            return []

        from app.repositories import dashboard_repository
        from app.repositories import dashboard_share_repository
        from app.repositories import group_member_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'list_by_owner',
            mock_list_func
        ), patch.object(
            dashboard_share_repository.DashboardShareRepository,
            'list_by_target',
            mock_list_by_target
        ), patch.object(
            group_member_repository.GroupMemberRepository,
            'list_groups_for_user',
            mock_list_groups
        ):
            response = authenticated_client.get("/api/dashboards")

            assert response.status_code == 200
            response_data = response.json()
            assert "data" in response_data
            assert "pagination" in response_data
            data = response_data["data"]
            assert len(data) == 1
            assert data[0]["id"] == sample_dashboard.id
            assert data[0]["name"] == sample_dashboard.name
            assert data[0]["my_permission"] == "owner"

    def test_list_dashboards_empty(
        self, authenticated_client: TestClient
    ) -> None:
        """Test listing dashboards returns empty list."""
        async def mock_list_func(self, owner_id, dynamodb):
            return []

        async def mock_list_by_target(self, shared_to_id, dynamodb):
            return []

        async def mock_list_groups(self, user_id, dynamodb):
            return []

        from app.repositories import dashboard_repository
        from app.repositories import dashboard_share_repository
        from app.repositories import group_member_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'list_by_owner',
            mock_list_func
        ), patch.object(
            dashboard_share_repository.DashboardShareRepository,
            'list_by_target',
            mock_list_by_target
        ), patch.object(
            group_member_repository.GroupMemberRepository,
            'list_groups_for_user',
            mock_list_groups
        ):
            response = authenticated_client.get("/api/dashboards")

            assert response.status_code == 200
            response_data = response.json()
            assert "data" in response_data
            assert "pagination" in response_data
            data = response_data["data"]
            assert len(data) == 0

    def test_list_dashboards_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test listing dashboards requires authentication."""
        response = unauthenticated_client.get("/api/dashboards")
        assert response.status_code == 403


class TestCreateDashboard:
    """Tests for POST /api/dashboards."""

    def test_create_dashboard_minimal(
        self, authenticated_client: TestClient, mock_user: User
    ) -> None:
        """Test creating dashboard with minimal fields."""
        new_dashboard = Dashboard(
            id="dash_new",
            name="New Dashboard",
            description=None,
            layout=None,
            filters=None,
            owner_id=mock_user.id,
            default_filter_view_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        async def mock_create_func(self, data, dynamodb):
            return new_dashboard

        from app.repositories import dashboard_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'create',
            mock_create_func
        ):
            response = authenticated_client.post(
                "/api/dashboards",
                json={"name": "New Dashboard"}
            )

            assert response.status_code == 201
            response_data = response.json()
            assert "data" in response_data
            data = response_data["data"]
            assert data["name"] == "New Dashboard"
            assert data["owner_id"] == mock_user.id

    def test_create_dashboard_with_layout_and_filters(
        self, authenticated_client: TestClient, mock_user: User, sample_layout, sample_filters
    ) -> None:
        """Test creating dashboard with layout and filters."""
        new_dashboard = Dashboard(
            id="dash_new",
            name="New Dashboard",
            description="With layout",
            layout=sample_layout,
            filters=sample_filters,
            owner_id=mock_user.id,
            default_filter_view_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        async def mock_create_func(self, data, dynamodb):
            return new_dashboard

        from app.repositories import dashboard_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'create',
            mock_create_func
        ):
            response = authenticated_client.post(
                "/api/dashboards",
                json={
                    "name": "New Dashboard",
                    "description": "With layout",
                    "layout": [
                        {"card_id": "card_1", "x": 0, "y": 0, "w": 4, "h": 3},
                        {"card_id": "card_2", "x": 4, "y": 0, "w": 4, "h": 3},
                    ],
                    "filters": [
                        {
                            "id": "filter_1",
                            "type": "select",
                            "column": "category",
                            "label": "Category",
                            "multi_select": True,
                        }
                    ]
                }
            )

            assert response.status_code == 201
            response_data = response.json()
            assert "data" in response_data
            data = response_data["data"]
            assert data["name"] == "New Dashboard"
            assert len(data["layout"]) == 2
            assert len(data["filters"]) == 1

    def test_create_dashboard_empty_name(
        self, authenticated_client: TestClient
    ) -> None:
        """Test creating dashboard with empty name fails."""
        response = authenticated_client.post(
            "/api/dashboards",
            json={"name": ""}
        )

        assert response.status_code == 422

    def test_create_dashboard_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test creating dashboard requires authentication."""
        response = unauthenticated_client.post(
            "/api/dashboards",
            json={"name": "Test"}
        )
        assert response.status_code == 403


class TestGetDashboard:
    """Tests for GET /api/dashboards/{dashboard_id}."""

    def test_get_dashboard_success(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """Test getting dashboard by ID."""
        async def mock_get_func(self, dashboard_id, dynamodb):
            return sample_dashboard

        async def mock_assert_perm(self, dashboard, user_id, required, dynamodb):
            pass  # Owner has access

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert_perm
        ):
            response = authenticated_client.get(f"/api/dashboards/{sample_dashboard.id}")

            assert response.status_code == 200
            response_data = response.json()
            assert "data" in response_data
            data = response_data["data"]
            assert data["id"] == sample_dashboard.id
            assert data["name"] == sample_dashboard.name

    def test_get_dashboard_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test getting non-existent dashboard returns 404."""
        async def mock_get_func(self, dashboard_id, dynamodb):
            return None

        from app.repositories import dashboard_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ):
            response = authenticated_client.get("/api/dashboards/nonexistent")

            assert response.status_code == 404

    def test_get_dashboard_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test getting dashboard requires authentication."""
        response = unauthenticated_client.get("/api/dashboards/dash_123")
        assert response.status_code == 403


class TestUpdateDashboard:
    """Tests for PUT /api/dashboards/{dashboard_id}."""

    def test_update_dashboard_success(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """Test updating dashboard successfully."""
        updated_dashboard = Dashboard(
            id=sample_dashboard.id,
            name="Updated Name",
            description=sample_dashboard.description,
            layout=sample_dashboard.layout,
            filters=sample_dashboard.filters,
            owner_id=sample_dashboard.owner_id,
            default_filter_view_id=sample_dashboard.default_filter_view_id,
            created_at=sample_dashboard.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        async def mock_get_func(self, dashboard_id, dynamodb):
            return sample_dashboard

        async def mock_update_func(self, dashboard_id, data, dynamodb):
            return updated_dashboard

        async def mock_assert_perm(self, dashboard, user_id, required, dynamodb):
            pass  # Owner has editor access

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ), patch.object(
            dashboard_repository.DashboardRepository,
            'update',
            mock_update_func
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert_perm
        ):
            response = authenticated_client.put(
                f"/api/dashboards/{sample_dashboard.id}",
                json={"name": "Updated Name"}
            )

            assert response.status_code == 200
            response_data = response.json()
            assert "data" in response_data
            data = response_data["data"]
            assert data["name"] == "Updated Name"

    def test_update_dashboard_not_owner(
        self, authenticated_client: TestClient, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test updating dashboard not owned returns 403."""
        from fastapi import HTTPException

        async def mock_get_func(self, dashboard_id, dynamodb):
            return sample_dashboard_other_owner

        async def mock_assert_perm(self, dashboard, user_id, required, dynamodb):
            raise HTTPException(status_code=403, detail="Requires editor permission or higher")

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert_perm
        ):
            response = authenticated_client.put(
                f"/api/dashboards/{sample_dashboard_other_owner.id}",
                json={"name": "Try Update"}
            )

            assert response.status_code == 403

    def test_update_dashboard_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test updating non-existent dashboard returns 404."""
        async def mock_get_func(self, dashboard_id, dynamodb):
            return None

        from app.repositories import dashboard_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ):
            response = authenticated_client.put(
                "/api/dashboards/nonexistent",
                json={"name": "Try Update"}
            )

            assert response.status_code == 404

    def test_update_dashboard_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test updating dashboard requires authentication."""
        response = unauthenticated_client.put(
            "/api/dashboards/dash_123",
            json={"name": "Test"}
        )
        assert response.status_code == 403


class TestDeleteDashboard:
    """Tests for DELETE /api/dashboards/{dashboard_id}."""

    def test_delete_dashboard_success(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """Test deleting dashboard successfully."""
        async def mock_get_func(self, dashboard_id, dynamodb):
            return sample_dashboard

        async def mock_delete_func(self, dashboard_id, dynamodb):
            return None

        async def mock_assert_perm(self, dashboard, user_id, required, dynamodb):
            pass  # Owner has access

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ), patch.object(
            dashboard_repository.DashboardRepository,
            'delete',
            mock_delete_func
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert_perm
        ):
            response = authenticated_client.delete(f"/api/dashboards/{sample_dashboard.id}")

            assert response.status_code == 204

    def test_delete_dashboard_not_owner(
        self, authenticated_client: TestClient, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test deleting dashboard not owned returns 403."""
        from fastapi import HTTPException

        async def mock_get_func(self, dashboard_id, dynamodb):
            return sample_dashboard_other_owner

        async def mock_assert_perm(self, dashboard, user_id, required, dynamodb):
            raise HTTPException(status_code=403, detail="Requires owner permission or higher")

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert_perm
        ):
            response = authenticated_client.delete(
                f"/api/dashboards/{sample_dashboard_other_owner.id}"
            )

            assert response.status_code == 403

    def test_delete_dashboard_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test deleting non-existent dashboard returns 404."""
        async def mock_get_func(self, dashboard_id, dynamodb):
            return None

        from app.repositories import dashboard_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ):
            response = authenticated_client.delete("/api/dashboards/nonexistent")

            assert response.status_code == 404

    def test_delete_dashboard_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test deleting dashboard requires authentication."""
        response = unauthenticated_client.delete("/api/dashboards/dash_123")
        assert response.status_code == 403


class TestGetReferencedDatasets:
    """Tests for GET /api/dashboards/{dashboard_id}/referenced-datasets."""

    def test_get_referenced_datasets_success(
        self, authenticated_client: TestClient, sample_dashboard: Dashboard
    ) -> None:
        """Test getting referenced datasets successfully."""
        referenced_datasets = [
            {
                'dataset_id': 'ds_1',
                'name': 'Dataset 1',
                'row_count': 100,
                'used_by_cards': ['card_1']
            },
            {
                'dataset_id': 'ds_2',
                'name': 'Dataset 2',
                'row_count': 200,
                'used_by_cards': ['card_2']
            }
        ]

        async def mock_get_func(self, dashboard_id, dynamodb):
            return sample_dashboard

        async def mock_get_referenced_func(self, dashboard, dynamodb):
            return referenced_datasets

        async def mock_assert_perm(self, dashboard, user_id, required, dynamodb):
            pass  # Owner has viewer access

        from app.repositories import dashboard_repository
        from app.services import dashboard_service
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ), patch.object(
            dashboard_service.DashboardService,
            'get_referenced_datasets',
            mock_get_referenced_func
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert_perm
        ):
            response = authenticated_client.get(
                f"/api/dashboards/{sample_dashboard.id}/referenced-datasets"
            )

            assert response.status_code == 200
            response_data = response.json()
            assert "data" in response_data
            data = response_data["data"]
            assert len(data) == 2
            assert data[0]['dataset_id'] == 'ds_1'
            assert data[1]['dataset_id'] == 'ds_2'

    def test_get_referenced_datasets_empty_layout(
        self, authenticated_client: TestClient, sample_dashboard_no_layout: Dashboard
    ) -> None:
        """Test getting referenced datasets with no layout returns empty."""
        async def mock_get_func(self, dashboard_id, dynamodb):
            return sample_dashboard_no_layout

        async def mock_get_referenced_func(self, dashboard, dynamodb):
            return []

        async def mock_assert_perm(self, dashboard, user_id, required, dynamodb):
            pass  # Owner has viewer access

        from app.repositories import dashboard_repository
        from app.services import dashboard_service
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ), patch.object(
            dashboard_service.DashboardService,
            'get_referenced_datasets',
            mock_get_referenced_func
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert_perm
        ):
            response = authenticated_client.get(
                f"/api/dashboards/{sample_dashboard_no_layout.id}/referenced-datasets"
            )

            assert response.status_code == 200
            response_data = response.json()
            assert "data" in response_data
            data = response_data["data"]
            assert len(data) == 0

    def test_get_referenced_datasets_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test getting referenced datasets for non-existent dashboard returns 404."""
        async def mock_get_func(self, dashboard_id, dynamodb):
            return None

        from app.repositories import dashboard_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ):
            response = authenticated_client.get(
                "/api/dashboards/nonexistent/referenced-datasets"
            )

            assert response.status_code == 404

    def test_get_referenced_datasets_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test getting referenced datasets requires authentication."""
        response = unauthenticated_client.get(
            "/api/dashboards/dash_123/referenced-datasets"
        )
        assert response.status_code == 403


class TestCloneDashboard:
    """Tests for POST /api/dashboards/{dashboard_id}/clone."""

    def test_clone_dashboard_success(
        self, authenticated_client: TestClient, mock_user: User, sample_dashboard: Dashboard
    ) -> None:
        """Test successful dashboard cloning."""
        cloned_dashboard = Dashboard(
            id="dash_cloned",
            name=f"{sample_dashboard.name} (Copy)",
            description=sample_dashboard.description,
            layout=sample_dashboard.layout,
            filters=sample_dashboard.filters,
            owner_id=mock_user.id,
            default_filter_view_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        async def mock_get_func(self, dashboard_id, dynamodb):
            return sample_dashboard

        async def mock_create_func(self, data, dynamodb):
            return cloned_dashboard

        async def mock_assert_perm(self, dashboard, user_id, required, dynamodb):
            pass  # Owner has viewer access

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ), patch.object(
            dashboard_repository.DashboardRepository,
            'create',
            mock_create_func
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert_perm
        ):
            response = authenticated_client.post(
                f"/api/dashboards/{sample_dashboard.id}/clone"
            )

            assert response.status_code == 201
            response_data = response.json()
            assert "data" in response_data
            data = response_data["data"]
            assert data["id"] == "dash_cloned"
            assert data["name"] == f"{sample_dashboard.name} (Copy)"
            assert data["description"] == sample_dashboard.description
            assert data["owner_id"] == mock_user.id

    def test_clone_dashboard_not_found(
        self, authenticated_client: TestClient
    ) -> None:
        """Test cloning non-existent dashboard returns 404."""
        async def mock_get_func(self, dashboard_id, dynamodb):
            return None

        from app.repositories import dashboard_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_func
        ):
            response = authenticated_client.post(
                "/api/dashboards/nonexistent/clone"
            )

            assert response.status_code == 404

    def test_clone_dashboard_unauthenticated(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Test cloning dashboard requires authentication."""
        response = unauthenticated_client.post(
            "/api/dashboards/dash_123/clone"
        )
        assert response.status_code == 403


class TestDashboardPermissions:
    """Tests for permission-based access control."""

    def test_get_dashboard_viewer_allowed(
        self, authenticated_client: TestClient, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test viewer can access dashboard."""
        async def mock_get(self, did, dynamodb):
            return sample_dashboard_other_owner

        async def mock_assert(self, dashboard, user_id, required, dynamodb):
            pass  # Allow access (viewer permission granted)

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert
        ):
            response = authenticated_client.get(
                f"/api/dashboards/{sample_dashboard_other_owner.id}"
            )
            assert response.status_code == 200

    def test_get_dashboard_no_permission(
        self, authenticated_client: TestClient, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test user without permission gets 403."""
        from fastapi import HTTPException

        async def mock_get(self, did, dynamodb):
            return sample_dashboard_other_owner

        async def mock_assert(self, dashboard, user_id, required, dynamodb):
            raise HTTPException(status_code=403, detail="No access")

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert
        ):
            response = authenticated_client.get(
                f"/api/dashboards/{sample_dashboard_other_owner.id}"
            )
            assert response.status_code == 403

    def test_update_dashboard_editor_allowed(
        self, authenticated_client: TestClient, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test editor can update dashboard."""
        updated = Dashboard(
            id=sample_dashboard_other_owner.id,
            name="Updated",
            owner_id=sample_dashboard_other_owner.owner_id,
            default_filter_view_id=None,
            created_at=sample_dashboard_other_owner.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        async def mock_get(self, did, dynamodb):
            return sample_dashboard_other_owner

        async def mock_assert(self, dashboard, user_id, required, dynamodb):
            pass  # Editor permission granted

        async def mock_update(self, did, data, dynamodb):
            return updated

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert
        ), patch.object(
            dashboard_repository.DashboardRepository,
            'update',
            mock_update
        ):
            response = authenticated_client.put(
                f"/api/dashboards/{sample_dashboard_other_owner.id}",
                json={"name": "Updated"}
            )
            assert response.status_code == 200

    def test_delete_dashboard_requires_owner(
        self, authenticated_client: TestClient, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test non-owner cannot delete dashboard."""
        from fastapi import HTTPException

        async def mock_get(self, did, dynamodb):
            return sample_dashboard_other_owner

        async def mock_assert(self, dashboard, user_id, required, dynamodb):
            raise HTTPException(status_code=403, detail="Owner only")

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert
        ):
            response = authenticated_client.delete(
                f"/api/dashboards/{sample_dashboard_other_owner.id}"
            )
            assert response.status_code == 403

    def test_clone_dashboard_viewer_allowed(
        self, authenticated_client: TestClient, mock_user: User, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test viewer can clone dashboard."""
        cloned = Dashboard(
            id="dash_cloned",
            name=f"{sample_dashboard_other_owner.name} (Copy)",
            owner_id=mock_user.id,
            default_filter_view_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        async def mock_get(self, did, dynamodb):
            return sample_dashboard_other_owner

        async def mock_assert(self, dashboard, user_id, required, dynamodb):
            pass  # Viewer permission granted

        async def mock_create(self, data, dynamodb):
            return cloned

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert
        ), patch.object(
            dashboard_repository.DashboardRepository,
            'create',
            mock_create
        ):
            response = authenticated_client.post(
                f"/api/dashboards/{sample_dashboard_other_owner.id}/clone"
            )
            assert response.status_code == 201

    def test_referenced_datasets_no_permission(
        self, authenticated_client: TestClient, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test user without permission cannot access referenced datasets."""
        from fastapi import HTTPException

        async def mock_get(self, did, dynamodb):
            return sample_dashboard_other_owner

        async def mock_assert(self, dashboard, user_id, required, dynamodb):
            raise HTTPException(status_code=403, detail="No access")

        from app.repositories import dashboard_repository
        from app.services import permission_service

        with patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get
        ), patch.object(
            permission_service.PermissionService,
            'assert_permission',
            mock_assert
        ):
            response = authenticated_client.get(
                f"/api/dashboards/{sample_dashboard_other_owner.id}/referenced-datasets"
            )
            assert response.status_code == 403

    def test_list_dashboards_includes_shared(
        self, authenticated_client: TestClient, mock_user: User,
        sample_dashboard: Dashboard, sample_dashboard_other_owner: Dashboard
    ) -> None:
        """Test list includes shared dashboards with my_permission."""
        from app.models.dashboard_share import DashboardShare, SharedToType

        shared_entry = DashboardShare(
            id="share_1",
            dashboard_id=sample_dashboard_other_owner.id,
            shared_to_type=SharedToType.USER,
            shared_to_id=mock_user.id,
            permission=Permission.VIEWER,
            shared_by="user_456",
            created_at=datetime.now(timezone.utc),
        )

        async def mock_list_by_owner(self, owner_id, dynamodb):
            return [sample_dashboard]

        async def mock_list_by_target(self, shared_to_id, dynamodb):
            if shared_to_id == mock_user.id:
                return [shared_entry]
            return []

        async def mock_list_groups(self, user_id, dynamodb):
            return []

        async def mock_get_by_id(self, dashboard_id, dynamodb):
            if dashboard_id == sample_dashboard_other_owner.id:
                return sample_dashboard_other_owner
            return None

        from app.repositories import dashboard_repository
        from app.repositories import dashboard_share_repository
        from app.repositories import group_member_repository

        with patch.object(
            dashboard_repository.DashboardRepository,
            'list_by_owner',
            mock_list_by_owner
        ), patch.object(
            dashboard_share_repository.DashboardShareRepository,
            'list_by_target',
            mock_list_by_target
        ), patch.object(
            group_member_repository.GroupMemberRepository,
            'list_groups_for_user',
            mock_list_groups
        ), patch.object(
            dashboard_repository.DashboardRepository,
            'get_by_id',
            mock_get_by_id
        ):
            response = authenticated_client.get("/api/dashboards")

            assert response.status_code == 200
            response_data = response.json()
            data = response_data["data"]
            assert len(data) == 2

            # Find own and shared dashboards
            own = next(d for d in data if d["id"] == sample_dashboard.id)
            shared = next(d for d in data if d["id"] == sample_dashboard_other_owner.id)

            assert own["my_permission"] == "owner"
            assert shared["my_permission"] == "viewer"
