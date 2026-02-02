"""Tests for FilterView API routes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastapi import HTTPException, status as http_status

from app.api import deps


class TestFilterViewRoutes:
    """Tests for FilterView CRUD API endpoints."""

    @pytest.fixture
    def mock_current_user(self):
        from app.models.user import User
        return User(
            id="user_test123",
            email="test@example.com",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def authed_client(self, client, mock_current_user):
        from app.main import app

        async def override_get_current_user():
            return mock_current_user

        async def override_get_dynamodb_resource():
            yield MagicMock()

        app.dependency_overrides[deps.get_current_user] = override_get_current_user
        app.dependency_overrides[deps.get_dynamodb_resource] = override_get_dynamodb_resource

        yield client
        app.dependency_overrides.clear()

    def _mock_filter_view(self, **overrides):
        """Helper to create a mock FilterView."""
        defaults = {
            "id": "fv_abc123",
            "dashboard_id": "dashboard_xyz",
            "name": "Test View",
            "owner_id": "user_test123",
            "filter_state": {"category": "sales"},
            "is_shared": False,
            "is_default": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        mock = MagicMock()
        mock.model_dump.return_value = defaults
        for k, v in defaults.items():
            setattr(mock, k, v)
        return mock

    def _mock_dashboard(self, **overrides):
        """Helper to create a mock Dashboard."""
        defaults = {
            "id": "dashboard_xyz",
            "name": "Test Dashboard",
            "owner_id": "user_test123",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        mock = MagicMock()
        for k, v in defaults.items():
            setattr(mock, k, v)
        return mock

    # --- List filter views ---

    def test_list_filter_views(self, authed_client):
        """Test listing filter views for a dashboard with viewer permission."""
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
            patch("app.api.routes.filter_views.FilterViewRepository") as MockRepo,
        ):
            mock_dashboard = self._mock_dashboard()
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)
            MockPermSvc.return_value.assert_permission = AsyncMock(return_value=None)
            mock_fv = self._mock_filter_view()
            MockRepo.return_value.list_by_dashboard = AsyncMock(return_value=[mock_fv])

            response = authed_client.get("/api/dashboards/dashboard_xyz/filter-views")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Test View"

    def test_list_filter_views_empty(self, authed_client):
        """Test listing filter views returns empty list."""
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
            patch("app.api.routes.filter_views.FilterViewRepository") as MockRepo,
        ):
            mock_dashboard = self._mock_dashboard()
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)
            MockPermSvc.return_value.assert_permission = AsyncMock(return_value=None)
            MockRepo.return_value.list_by_dashboard = AsyncMock(return_value=[])

            response = authed_client.get("/api/dashboards/dashboard_xyz/filter-views")

        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_list_filter_views_unauthenticated(self, client):
        """Test listing without auth returns 401/403."""
        response = client.get("/api/dashboards/dashboard_xyz/filter-views")
        assert response.status_code in (401, 403)

    def test_list_filter_views_dashboard_not_found(self, authed_client):
        """Test listing filter views for non-existent dashboard returns 404."""
        with patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo:
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=None)

            response = authed_client.get("/api/dashboards/nonexistent/filter-views")

        assert response.status_code == 404

    def test_list_filter_views_no_permission(self, authed_client):
        """Test listing filter views without viewer permission returns 403."""
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
        ):
            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)
            MockPermSvc.return_value.assert_permission = AsyncMock(
                side_effect=HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Requires viewer permission or higher",
                )
            )

            response = authed_client.get("/api/dashboards/dashboard_xyz/filter-views")

        assert response.status_code == 403

    # --- Create filter view ---

    def test_create_filter_view(self, authed_client):
        """Test creating a filter view with editor permission."""
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
            patch("app.api.routes.filter_views.FilterViewRepository") as MockRepo,
        ):
            mock_dashboard = self._mock_dashboard()
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)
            MockPermSvc.return_value.assert_permission = AsyncMock(return_value=None)
            mock_fv = self._mock_filter_view()
            MockRepo.return_value.create = AsyncMock(return_value=mock_fv)

            response = authed_client.post(
                "/api/dashboards/dashboard_xyz/filter-views",
                json={
                    "name": "New View",
                    "filter_state": {"category": "sales"},
                },
            )

        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Test View"

    def test_create_filter_view_validation_error(self, authed_client):
        """Test creating with invalid data returns 422."""
        response = authed_client.post(
            "/api/dashboards/dashboard_xyz/filter-views",
            json={"name": ""},
        )
        assert response.status_code == 422

    def test_create_filter_view_unauthenticated(self, client):
        """Test creating without auth returns 401/403."""
        response = client.post(
            "/api/dashboards/dashboard_xyz/filter-views",
            json={"name": "Test", "filter_state": {}},
        )
        assert response.status_code in (401, 403)

    def test_create_filter_view_dashboard_not_found(self, authed_client):
        """Test creating filter view for non-existent dashboard returns 404."""
        with patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo:
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=None)

            response = authed_client.post(
                "/api/dashboards/nonexistent/filter-views",
                json={
                    "name": "New View",
                    "filter_state": {"category": "sales"},
                },
            )

        assert response.status_code == 404

    def test_create_filter_view_viewer_only_forbidden(self, authed_client):
        """Test creating filter view with only viewer permission returns 403."""
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
        ):
            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)
            MockPermSvc.return_value.assert_permission = AsyncMock(
                side_effect=HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Requires editor permission or higher",
                )
            )

            response = authed_client.post(
                "/api/dashboards/dashboard_xyz/filter-views",
                json={
                    "name": "New View",
                    "filter_state": {"category": "sales"},
                },
            )

        assert response.status_code == 403

    # --- Get filter view ---

    def test_get_filter_view(self, authed_client):
        """Test getting a filter view by ID."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            mock_fv = self._mock_filter_view()
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            response = authed_client.get("/api/filter-views/fv_abc123")

        assert response.status_code == 200
        assert response.json()["data"]["id"] == "fv_abc123"

    def test_get_filter_view_not_found(self, authed_client):
        """Test getting non-existent filter view returns 404."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            MockRepo.return_value.get_by_id = AsyncMock(return_value=None)

            response = authed_client.get("/api/filter-views/fv_nonexistent")

        assert response.status_code == 404

    def test_get_filter_view_unauthenticated(self, client):
        """Test getting without auth returns 401/403."""
        response = client.get("/api/filter-views/fv_abc123")
        assert response.status_code in (401, 403)

    # --- Update filter view ---

    def test_update_filter_view(self, authed_client):
        """Test updating a filter view."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            mock_fv = self._mock_filter_view()
            updated_fv = self._mock_filter_view(name="Updated")
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)
            MockRepo.return_value.update = AsyncMock(return_value=updated_fv)

            response = authed_client.put(
                "/api/filter-views/fv_abc123",
                json={"name": "Updated"},
            )

        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated"

    def test_update_filter_view_forbidden(self, authed_client):
        """Test updating filter view owned by another user returns 403."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            mock_fv = self._mock_filter_view(owner_id="other_user")
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            response = authed_client.put(
                "/api/filter-views/fv_abc123",
                json={"name": "Updated"},
            )

        assert response.status_code == 403

    def test_update_filter_view_not_found(self, authed_client):
        """Test updating non-existent filter view returns 404."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            MockRepo.return_value.get_by_id = AsyncMock(return_value=None)

            response = authed_client.put(
                "/api/filter-views/fv_nonexistent",
                json={"name": "Updated"},
            )

        assert response.status_code == 404

    def test_update_filter_view_unauthenticated(self, client):
        """Test updating without auth returns 401/403."""
        response = client.put(
            "/api/filter-views/fv_abc123",
            json={"name": "Updated"},
        )
        assert response.status_code in (401, 403)

    # --- Delete filter view ---

    def test_delete_filter_view(self, authed_client):
        """Test deleting a filter view."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            mock_fv = self._mock_filter_view()
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)
            MockRepo.return_value.delete = AsyncMock()

            response = authed_client.delete("/api/filter-views/fv_abc123")

        assert response.status_code == 204

    def test_delete_filter_view_forbidden(self, authed_client):
        """Test deleting filter view owned by another user returns 403."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            mock_fv = self._mock_filter_view(owner_id="other_user")
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            response = authed_client.delete("/api/filter-views/fv_abc123")

        assert response.status_code == 403

    def test_delete_filter_view_not_found(self, authed_client):
        """Test deleting non-existent filter view returns 404."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            MockRepo.return_value.get_by_id = AsyncMock(return_value=None)

            response = authed_client.delete("/api/filter-views/fv_nonexistent")

        assert response.status_code == 404

    def test_delete_filter_view_unauthenticated(self, client):
        """Test deleting without auth returns 401/403."""
        response = client.delete("/api/filter-views/fv_abc123")
        assert response.status_code in (401, 403)
