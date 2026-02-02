"""Group API endpoint tests."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_user, get_dynamodb_resource
from app.models.user import User
from app.models.group import Group, GroupMember


@pytest.fixture
def admin_user():
    return User(
        id="admin_1",
        email="admin@example.com",
        role="admin",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def regular_user():
    return User(
        id="user_1",
        email="user@example.com",
        role="user",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_dynamodb():
    return MagicMock()


@pytest.fixture
def admin_client(admin_user, mock_dynamodb):
    async def override_get_current_user():
        return admin_user
    async def override_get_dynamodb_resource():
        yield mock_dynamodb
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_dynamodb_resource] = override_get_dynamodb_resource
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def regular_client(regular_user, mock_dynamodb):
    async def override_get_current_user():
        return regular_user
    async def override_get_dynamodb_resource():
        yield mock_dynamodb
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_dynamodb_resource] = override_get_dynamodb_resource
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_group():
    return Group(
        id="group_abc123",
        name="Engineering",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_members():
    now = datetime.now(timezone.utc)
    return [
        GroupMember(group_id="group_abc123", user_id="user_1", added_at=now),
        GroupMember(group_id="group_abc123", user_id="user_2", added_at=now),
    ]


class TestListGroups:
    def test_list_groups_admin(self, admin_client, sample_group):
        async def mock_list(self, dynamodb):
            return [sample_group]
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'list_all', mock_list):
            response = admin_client.get("/api/groups")
            assert response.status_code == 200
            data = response.json()["data"]
            assert len(data) == 1

    def test_list_groups_non_admin_forbidden(self, regular_client):
        response = regular_client.get("/api/groups")
        assert response.status_code == 403


class TestCreateGroup:
    def test_create_group_admin(self, admin_client, sample_group):
        async def mock_get_by_name(self, name, dynamodb):
            return None
        async def mock_create(self, data, dynamodb):
            return sample_group
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_name', mock_get_by_name), \
             patch.object(group_repository.GroupRepository, 'create', mock_create):
            response = admin_client.post("/api/groups", json={"name": "Engineering"})
            assert response.status_code == 201

    def test_create_group_duplicate_name(self, admin_client, sample_group):
        async def mock_get_by_name(self, name, dynamodb):
            return sample_group
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_name', mock_get_by_name):
            response = admin_client.post("/api/groups", json={"name": "Engineering"})
            assert response.status_code == 409

    def test_create_group_non_admin_forbidden(self, regular_client):
        response = regular_client.post("/api/groups", json={"name": "Test"})
        assert response.status_code == 403


class TestGetGroup:
    def test_get_group_admin(self, admin_client, sample_group, sample_members):
        async def mock_get(self, gid, dynamodb):
            return sample_group
        async def mock_list_members(self, gid, dynamodb):
            return sample_members
        from app.repositories import group_repository, group_member_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get), \
             patch.object(group_member_repository.GroupMemberRepository, 'list_members', mock_list_members):
            response = admin_client.get("/api/groups/group_abc123")
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["id"] == "group_abc123"
            assert "members" in data

    def test_get_group_not_found(self, admin_client):
        async def mock_get(self, gid, dynamodb):
            return None
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get):
            response = admin_client.get("/api/groups/nonexistent")
            assert response.status_code == 404


class TestUpdateGroup:
    def test_update_group_admin(self, admin_client, sample_group):
        updated_group = Group(
            id="group_abc123", name="New Name",
            created_at=sample_group.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        async def mock_get(self, gid, dynamodb):
            return sample_group
        async def mock_get_by_name(self, name, dynamodb):
            return None
        async def mock_update(self, gid, data, dynamodb):
            return updated_group
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get), \
             patch.object(group_repository.GroupRepository, 'get_by_name', mock_get_by_name), \
             patch.object(group_repository.GroupRepository, 'update', mock_update):
            response = admin_client.put("/api/groups/group_abc123", json={"name": "New Name"})
            assert response.status_code == 200

    def test_update_group_not_found(self, admin_client):
        async def mock_get(self, gid, dynamodb):
            return None
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get):
            response = admin_client.put("/api/groups/nonexistent", json={"name": "X"})
            assert response.status_code == 404


class TestDeleteGroup:
    def test_delete_group_admin(self, admin_client, sample_group):
        async def mock_get(self, gid, dynamodb):
            return sample_group
        async def mock_delete(self, gid, dynamodb):
            return None
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get), \
             patch.object(group_repository.GroupRepository, 'delete', mock_delete):
            response = admin_client.delete("/api/groups/group_abc123")
            assert response.status_code == 204

    def test_delete_group_not_found(self, admin_client):
        async def mock_get(self, gid, dynamodb):
            return None
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get):
            response = admin_client.delete("/api/groups/nonexistent")
            assert response.status_code == 404


class TestAddMember:
    def test_add_member_admin(self, admin_client, sample_group):
        member = GroupMember(group_id="group_abc123", user_id="user_1", added_at=datetime.now(timezone.utc))
        async def mock_get(self, gid, dynamodb):
            return sample_group
        async def mock_add(self, gid, uid, dynamodb):
            return member
        from app.repositories import group_repository, group_member_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get), \
             patch.object(group_member_repository.GroupMemberRepository, 'add_member', mock_add):
            response = admin_client.post("/api/groups/group_abc123/members", json={"user_id": "user_1"})
            assert response.status_code == 201

    def test_add_member_group_not_found(self, admin_client):
        async def mock_get(self, gid, dynamodb):
            return None
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get):
            response = admin_client.post("/api/groups/nonexistent/members", json={"user_id": "user_1"})
            assert response.status_code == 404


class TestRemoveMember:
    def test_remove_member_admin(self, admin_client, sample_group):
        async def mock_get(self, gid, dynamodb):
            return sample_group
        async def mock_remove(self, gid, uid, dynamodb):
            return None
        from app.repositories import group_repository, group_member_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get), \
             patch.object(group_member_repository.GroupMemberRepository, 'remove_member', mock_remove):
            response = admin_client.delete("/api/groups/group_abc123/members/user_1")
            assert response.status_code == 204

    def test_remove_member_group_not_found(self, admin_client):
        async def mock_get(self, gid, dynamodb):
            return None
        from app.repositories import group_repository
        with patch.object(group_repository.GroupRepository, 'get_by_id', mock_get):
            response = admin_client.delete("/api/groups/nonexistent/members/user_1")
            assert response.status_code == 404
