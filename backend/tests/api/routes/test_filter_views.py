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

    # --- List visibility filtering tests ---

    def test_list_filter_views_returns_own_private_views(self, authed_client, mock_current_user):
        """Test that user's own private views (is_shared=False) are visible in the list."""
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
            patch("app.api.routes.filter_views.FilterViewRepository") as MockRepo,
        ):
            mock_dashboard = self._mock_dashboard()
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)
            MockPermSvc.return_value.assert_permission = AsyncMock(return_value=None)

            # User's own private view (is_shared=False, owner_id=current_user.id)
            own_private_view = self._mock_filter_view(
                id="fv_own_private",
                name="My Private View",
                owner_id=mock_current_user.id,
                is_shared=False,
            )
            MockRepo.return_value.list_by_dashboard = AsyncMock(return_value=[own_private_view])

            response = authed_client.get("/api/dashboards/dashboard_xyz/filter-views")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == "fv_own_private"
        assert data[0]["name"] == "My Private View"
        assert data[0]["is_shared"] is False

    def test_list_filter_views_returns_shared_views_with_permission(self, authed_client):
        """Test that other user's shared views (is_shared=True) are visible when user has dashboard permission."""
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
            patch("app.api.routes.filter_views.FilterViewRepository") as MockRepo,
        ):
            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)
            MockPermSvc.return_value.assert_permission = AsyncMock(return_value=None)

            # Other user's shared view (is_shared=True, owner_id != current_user.id)
            other_shared_view = self._mock_filter_view(
                id="fv_other_shared",
                name="Other User Shared View",
                owner_id="other_user",
                is_shared=True,
            )
            MockRepo.return_value.list_by_dashboard = AsyncMock(return_value=[other_shared_view])

            response = authed_client.get("/api/dashboards/dashboard_xyz/filter-views")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == "fv_other_shared"
        assert data[0]["is_shared"] is True

    def test_list_filter_views_excludes_other_private_views(self, authed_client, mock_current_user):
        """Test that other user's private views (is_shared=False) are NOT visible."""
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
            patch("app.api.routes.filter_views.FilterViewRepository") as MockRepo,
        ):
            mock_dashboard = self._mock_dashboard()
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)
            MockPermSvc.return_value.assert_permission = AsyncMock(return_value=None)

            # Mix of views: own private, other's shared, other's private
            own_private_view = self._mock_filter_view(
                id="fv_own_private",
                name="My Private View",
                owner_id=mock_current_user.id,
                is_shared=False,
            )
            other_shared_view = self._mock_filter_view(
                id="fv_other_shared",
                name="Other Shared View",
                owner_id="other_user",
                is_shared=True,
            )
            other_private_view = self._mock_filter_view(
                id="fv_other_private",
                name="Other Private View",
                owner_id="other_user",
                is_shared=False,
            )

            # Repository returns all views (unfiltered)
            MockRepo.return_value.list_by_dashboard = AsyncMock(
                return_value=[own_private_view, other_shared_view, other_private_view]
            )

            response = authed_client.get("/api/dashboards/dashboard_xyz/filter-views")

        assert response.status_code == 200
        data = response.json()["data"]

        # Should only return own private view and other's shared view
        # Other's private view should be excluded
        returned_ids = [fv["id"] for fv in data]
        assert "fv_own_private" in returned_ids, "Own private view should be visible"
        assert "fv_other_shared" in returned_ids, "Other's shared view should be visible"
        assert "fv_other_private" not in returned_ids, "Other's private view should NOT be visible"
        assert len(data) == 2

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

    def test_get_own_private_view_allowed(self, authed_client):
        """Test getting own private filter view is allowed regardless of is_shared."""
        with patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo:
            # owner_id matches current user (user_test123), is_shared=False
            mock_fv = self._mock_filter_view(
                owner_id="user_test123",
                is_shared=False,
            )
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            response = authed_client.get("/api/filter-views/fv_abc123")

        assert response.status_code == 200
        assert response.json()["data"]["id"] == "fv_abc123"

    def test_get_shared_view_with_permission_allowed(self, authed_client):
        """Test getting another user's shared filter view is allowed with dashboard permission."""
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

    # --- Shared view permission tests ---

    def test_create_shared_view_requires_editor(self, authed_client):
        """Test creating a shared view (is_shared=True) requires EDITOR permission.

        When a user with VIEWER permission tries to create a shared view,
        the request should be rejected with 403.

        Permission rule: Shared view creation requires Dashboard EDITOR or higher.
        """
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
        ):
            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)

            # Simulate: user has VIEWER permission only
            # For shared views (is_shared=True), EDITOR should be required
            # For private views (is_shared=False), VIEWER should be sufficient
            def permission_check(dashboard, user_id, required_permission, dynamodb):
                from app.models.dashboard_share import Permission
                if required_permission == Permission.EDITOR:
                    raise HTTPException(
                        status_code=http_status.HTTP_403_FORBIDDEN,
                        detail="Requires editor permission to create shared views",
                    )
                # VIEWER check passes
                return None

            MockPermSvc.return_value.assert_permission = AsyncMock(side_effect=permission_check)

            response = authed_client.post(
                "/api/dashboards/dashboard_xyz/filter-views",
                json={
                    "name": "Shared View",
                    "filter_state": {"category": "sales"},
                    "is_shared": True,
                },
            )

        assert response.status_code == 403, (
            "Creating a shared view (is_shared=True) should require EDITOR permission"
        )

    def test_create_private_view_allowed_for_viewer(self, authed_client):
        """Test creating a private view (is_shared=False) is allowed with VIEWER permission.

        Users with only VIEWER permission should be able to create private filter views.

        Permission rule: Private view creation requires Dashboard VIEWER or higher.
        """
        with (
            patch("app.api.routes.filter_views.DashboardRepository") as MockDashRepo,
            patch("app.api.routes.filter_views.PermissionService") as MockPermSvc,
            patch("app.api.routes.filter_views.FilterViewRepository") as MockRepo,
        ):
            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)

            # Simulate: user has only VIEWER permission
            def permission_check(dashboard, user_id, required_permission, dynamodb):
                from app.models.dashboard_share import Permission
                if required_permission == Permission.EDITOR:
                    raise HTTPException(
                        status_code=http_status.HTTP_403_FORBIDDEN,
                        detail="Requires editor permission",
                    )
                # VIEWER check passes
                return None

            MockPermSvc.return_value.assert_permission = AsyncMock(side_effect=permission_check)

            mock_fv = self._mock_filter_view(is_shared=False)
            MockRepo.return_value.create = AsyncMock(return_value=mock_fv)

            response = authed_client.post(
                "/api/dashboards/dashboard_xyz/filter-views",
                json={
                    "name": "Private View",
                    "filter_state": {"category": "sales"},
                    "is_shared": False,
                },
            )

        assert response.status_code == 201, (
            "Creating a private view (is_shared=False) should be allowed with VIEWER permission"
        )

    def test_update_is_shared_requires_editor(self, authed_client):
        """Test updating is_shared attribute requires EDITOR permission.

        Owner can update other fields, but changing is_shared requires EDITOR permission.

        Permission rule: Changing is_shared requires owner + Dashboard EDITOR or higher.

        Note: This test uses create=True for patches because the implementation
        needs to be updated to import DashboardRepository and PermissionService.

        Current implementation does NOT check EDITOR permission for is_shared changes,
        so this test will FAIL until the implementation is updated.
        """
        with (
            patch("app.api.routes.filter_view_detail.FilterViewRepository") as MockRepo,
            patch("app.api.routes.filter_view_detail.DashboardRepository", create=True) as MockDashRepo,
            patch("app.api.routes.filter_view_detail.PermissionService", create=True) as MockPermSvc,
        ):
            # User owns the filter view
            mock_fv = self._mock_filter_view(owner_id="user_test123", is_shared=False)
            MockRepo.return_value.get_by_id = AsyncMock(return_value=mock_fv)

            # Mock update to return updated filter view (needed if permission check is not implemented)
            updated_fv = self._mock_filter_view(owner_id="user_test123", is_shared=True)
            MockRepo.return_value.update = AsyncMock(return_value=updated_fv)

            # Dashboard exists
            mock_dashboard = self._mock_dashboard(owner_id="other_user")
            MockDashRepo.return_value.get_by_id = AsyncMock(return_value=mock_dashboard)

            # User only has VIEWER permission on the dashboard
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

        assert response.status_code == 403, (
            "Changing is_shared should require EDITOR permission even if user is owner"
        )
