"""Tests for FilterView detail API routes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastapi import HTTPException, status as http_status

from app.api import deps


class TestFilterViewDetailRoutes:
    """Tests for FilterView GET/PUT/DELETE endpoints."""

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

    # --- GET filter view tests ---

    def test_get_filter_view_as_owner_success(self, authed_client):
        """Test getting filter view as owner succeeds."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            mock_fv = self._mock_filter_view()
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            response = authed_client.get("/api/filter-views/fv_abc123")

        assert response.status_code == 200
        assert response.json()["data"]["id"] == "fv_abc123"

    def test_get_shared_view_with_viewer_permission_success(self, authed_client):
        """Test getting another user's shared filter view with VIEWER permission succeeds."""
        with (
            patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo,
            patch("app.api.routes.filter_view_detail.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_view_detail.PermissionService") as MockPermSvc,
        ):
            # Different owner but is_shared=True
            mock_fv = self._mock_filter_view(
                owner_id="other_user",
                is_shared=True,
                dashboard_id="dashboard_xyz",
            )
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)

            # User has viewer permission
            MockPermSvc.return_value.assert_permission = AsyncMock(return_value=None)

            response = authed_client.get("/api/filter-views/fv_abc123")

        assert response.status_code == 200
        assert response.json()["data"]["id"] == "fv_abc123"

    def test_get_other_private_view_forbidden(self, authed_client):
        """Test getting another user's private filter view returns 403."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            # Different owner and is_shared=False
            mock_fv = self._mock_filter_view(
                owner_id="other_user",
                is_shared=False,
            )
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            response = authed_client.get("/api/filter-views/fv_abc123")

        assert response.status_code == 403

    def test_get_filter_view_not_found(self, authed_client):
        """Test getting non-existent filter view returns 404."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            MockRepo.return_value.get_by_id = AsyncMock(return_value=None)

            response = authed_client.get("/api/filter-views/fv_nonexistent")

        assert response.status_code == 404

    def test_get_filter_view_dashboard_not_found(self, authed_client):
        """Test getting shared filter view when dashboard doesn't exist returns 404."""
        with (
            patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo,
            patch("app.api.routes.filter_view_detail.DashboardRepository") as MockDashRepo,
        ):
            # Other user's shared view
            mock_fv = self._mock_filter_view(
                owner_id="other_user",
                is_shared=True,
                dashboard_id="dashboard_xyz",
            )
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            # Dashboard not found
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=None)

            response = authed_client.get("/api/filter-views/fv_abc123")

        assert response.status_code == 404

    def test_get_filter_view_unauthenticated(self, client):
        """Test getting without auth returns 401/403."""
        response = client.get("/api/filter-views/fv_abc123")
        assert response.status_code in (401, 403)

    # --- PUT filter view tests ---

    def test_update_filter_view_as_owner_success(self, authed_client):
        """Test updating a filter view as owner succeeds."""
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

    def test_update_is_shared_with_editor_permission_success(self, authed_client):
        """Test updating is_shared attribute with EDITOR permission succeeds."""
        with (
            patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo,
            patch("app.api.routes.filter_view_detail.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_view_detail.PermissionService") as MockPermSvc,
        ):
            # User owns the filter view
            mock_fv = self._mock_filter_view(owner_id="user_test123", is_shared=False)
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            # Updated filter view
            updated_fv = self._mock_filter_view(owner_id="user_test123", is_shared=True)
            MockRepo.return_value.update = AsyncMock(return_value=updated_fv)

            # Dashboard exists
            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)

            # User has EDITOR permission
            MockPermSvc.return_value.assert_permission = AsyncMock(return_value=None)

            response = authed_client.put(
                "/api/filter-views/fv_abc123",
                json={"is_shared": True},
            )

        assert response.status_code == 200
        assert response.json()["data"]["is_shared"] is True

    def test_update_is_shared_without_editor_permission_forbidden(self, authed_client):
        """Test updating is_shared attribute without EDITOR permission returns 403."""
        with (
            patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo,
            patch("app.api.routes.filter_view_detail.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_view_detail.PermissionService") as MockPermSvc,
        ):
            # User owns the filter view
            mock_fv = self._mock_filter_view(owner_id="user_test123", is_shared=False)
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            # Dashboard exists
            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)

            # User only has VIEWER permission
            def permission_check(dashboard, user_id, required_permission, dynamodb):
                from app.models.dashboard_share import Permission
                if required_permission == Permission.EDITOR:
                    raise HTTPException(
                        status_code=http_status.HTTP_403_FORBIDDEN,
                        detail="Requires editor permission to change is_shared",
                    )
                return None

            MockPermSvc.return_value.assert_permission = AsyncMock(side_effect=permission_check)

            response = authed_client.put(
                "/api/filter-views/fv_abc123",
                json={"is_shared": True},
            )

        assert response.status_code == 403

    def test_update_filter_view_as_non_owner_forbidden(self, authed_client):
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

    # --- DELETE filter view tests ---

    def test_delete_filter_view_as_owner_success(self, authed_client):
        """Test deleting a filter view as owner succeeds."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            mock_fv = self._mock_filter_view()
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)
            MockRepo.return_value.delete = AsyncMock()

            response = authed_client.delete("/api/filter-views/fv_abc123")

        assert response.status_code == 204

    def test_delete_filter_view_as_non_owner_forbidden(self, authed_client):
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
