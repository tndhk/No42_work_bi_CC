"""Dashboard Share API endpoint tests."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource
from app.models.user import User
from app.models.dashboard import Dashboard
from app.models.dashboard_share import DashboardShare, Permission, SharedToType


@pytest.fixture
def owner_user():
    return User(
        id="user_owner", email="owner@example.com", role="user",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def other_user():
    return User(
        id="user_other", email="other@example.com", role="user",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def mock_dynamodb():
    return MagicMock()

@pytest.fixture
def sample_dashboard():
    return Dashboard(
        id="dash_1", name="Test Dashboard", owner_id="user_owner",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def sample_share():
    return DashboardShare(
        id="share_1", dashboard_id="dash_1",
        shared_to_type=SharedToType.USER, shared_to_id="user_2",
        permission=Permission.VIEWER, shared_by="user_owner",
        created_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def owner_client(owner_user, mock_dynamodb):
    async def override_user():
        return owner_user
    async def override_db():
        yield mock_dynamodb
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_dynamodb_resource] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def other_client(other_user, mock_dynamodb):
    async def override_user():
        return other_user
    async def override_db():
        yield mock_dynamodb
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_dynamodb_resource] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestListShares:
    def test_list_shares_owner(self, owner_client, sample_dashboard, sample_share):
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        async def mock_list_shares(self, did, dynamodb):
            return [sample_share]
        from app.repositories import dashboard_repository, dashboard_share_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'list_by_dashboard', mock_list_shares):
            response = owner_client.get("/api/dashboards/dash_1/shares")
            assert response.status_code == 200
            data = response.json()["data"]
            assert len(data) == 1

    def test_list_shares_not_owner(self, other_client, sample_dashboard):
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        from app.repositories import dashboard_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash):
            response = other_client.get("/api/dashboards/dash_1/shares")
            assert response.status_code == 403

    def test_list_shares_dashboard_not_found(self, owner_client):
        async def mock_get_dash(self, did, dynamodb):
            return None
        from app.repositories import dashboard_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash):
            response = owner_client.get("/api/dashboards/nonexistent/shares")
            assert response.status_code == 404


class TestCreateShare:
    def test_create_share_owner(self, owner_client, sample_dashboard, sample_share):
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        async def mock_find_share(self, did, stype, sid, dynamodb):
            return None
        async def mock_create(self, data, dynamodb):
            return sample_share
        from app.repositories import dashboard_repository, dashboard_share_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'find_share', mock_find_share), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'create', mock_create):
            response = owner_client.post("/api/dashboards/dash_1/shares", json={
                "shared_to_type": "user",
                "shared_to_id": "user_2",
                "permission": "viewer",
            })
            assert response.status_code == 201

    def test_create_share_duplicate(self, owner_client, sample_dashboard, sample_share):
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        async def mock_find_share(self, did, stype, sid, dynamodb):
            return sample_share
        from app.repositories import dashboard_repository, dashboard_share_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'find_share', mock_find_share):
            response = owner_client.post("/api/dashboards/dash_1/shares", json={
                "shared_to_type": "user",
                "shared_to_id": "user_2",
                "permission": "viewer",
            })
            assert response.status_code == 409

    def test_create_share_not_owner(self, other_client, sample_dashboard):
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        from app.repositories import dashboard_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash):
            response = other_client.post("/api/dashboards/dash_1/shares", json={
                "shared_to_type": "user", "shared_to_id": "user_2", "permission": "viewer",
            })
            assert response.status_code == 403


class TestUpdateShare:
    def test_update_share_permission(self, owner_client, sample_dashboard, sample_share):
        updated_share = DashboardShare(
            id="share_1", dashboard_id="dash_1",
            shared_to_type=SharedToType.USER, shared_to_id="user_2",
            permission=Permission.EDITOR, shared_by="user_owner",
            created_at=sample_share.created_at,
        )
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        async def mock_get_share(self, sid, dynamodb):
            return sample_share
        async def mock_update(self, sid, data, dynamodb):
            return updated_share
        from app.repositories import dashboard_repository, dashboard_share_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'get_by_id', mock_get_share), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'update', mock_update):
            response = owner_client.put("/api/dashboards/dash_1/shares/share_1", json={
                "permission": "editor",
            })
            assert response.status_code == 200

    def test_update_share_not_found(self, owner_client, sample_dashboard):
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        async def mock_get_share(self, sid, dynamodb):
            return None
        from app.repositories import dashboard_repository, dashboard_share_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'get_by_id', mock_get_share):
            response = owner_client.put("/api/dashboards/dash_1/shares/nonexistent", json={
                "permission": "editor",
            })
            assert response.status_code == 404


class TestDeleteShare:
    def test_delete_share_owner(self, owner_client, sample_dashboard, sample_share):
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        async def mock_get_share(self, sid, dynamodb):
            return sample_share
        async def mock_delete(self, sid, dynamodb):
            return None
        from app.repositories import dashboard_repository, dashboard_share_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'get_by_id', mock_get_share), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'delete', mock_delete):
            response = owner_client.delete("/api/dashboards/dash_1/shares/share_1")
            assert response.status_code == 204

    def test_delete_share_not_found(self, owner_client, sample_dashboard):
        async def mock_get_dash(self, did, dynamodb):
            return sample_dashboard
        async def mock_get_share(self, sid, dynamodb):
            return None
        from app.repositories import dashboard_repository, dashboard_share_repository
        with patch.object(dashboard_repository.DashboardRepository, 'get_by_id', mock_get_dash), \
             patch.object(dashboard_share_repository.DashboardShareRepository, 'get_by_id', mock_get_share):
            response = owner_client.delete("/api/dashboards/dash_1/shares/nonexistent")
            assert response.status_code == 404
