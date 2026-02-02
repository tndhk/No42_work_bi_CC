"""Tests for Group models."""
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.models.group import Group, GroupCreate, GroupUpdate, GroupMember


class TestGroup:
    """Test Group model."""

    def test_group_valid(self):
        """Test creating Group with valid data."""
        group = Group(
            id="group_abc123",
            name="Engineering",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert group.id == "group_abc123"
        assert group.name == "Engineering"

    def test_group_timestamps(self):
        """Test Group has default timestamps."""
        group = Group(id="group_abc123", name="Engineering")
        assert group.created_at is not None
        assert group.updated_at is not None

    def test_group_serialization(self):
        """Test Group serialization to dict."""
        group = Group(id="group_abc123", name="Engineering")
        d = group.model_dump()
        assert d["id"] == "group_abc123"
        assert d["name"] == "Engineering"
        assert "created_at" in d
        assert "updated_at" in d


class TestGroupCreate:
    """Test GroupCreate model."""

    def test_group_create_valid(self):
        """Test creating GroupCreate with valid data."""
        gc = GroupCreate(name="Engineering")
        assert gc.name == "Engineering"

    def test_group_create_empty_name_fails(self):
        """Test GroupCreate validation fails with empty name."""
        with pytest.raises(ValidationError):
            GroupCreate(name="")

    def test_group_create_whitespace_name_fails(self):
        """Test GroupCreate validation fails with whitespace-only name."""
        with pytest.raises(ValidationError):
            GroupCreate(name="   ")

    def test_group_create_missing_name_fails(self):
        """Test GroupCreate validation fails without name."""
        with pytest.raises(ValidationError):
            GroupCreate()


class TestGroupUpdate:
    """Test GroupUpdate model."""

    def test_group_update_with_name(self):
        """Test GroupUpdate with name."""
        gu = GroupUpdate(name="New Name")
        assert gu.name == "New Name"

    def test_group_update_optional(self):
        """Test GroupUpdate with no fields."""
        gu = GroupUpdate()
        assert gu.name is None

    def test_group_update_empty_name_fails(self):
        """Test GroupUpdate validation fails with empty name."""
        with pytest.raises(ValidationError):
            GroupUpdate(name="")


class TestGroupMember:
    """Test GroupMember model."""

    def test_group_member_valid(self):
        """Test creating GroupMember with valid data."""
        gm = GroupMember(
            group_id="group_abc123",
            user_id="user_123",
            added_at=datetime.utcnow(),
        )
        assert gm.group_id == "group_abc123"
        assert gm.user_id == "user_123"
        assert gm.added_at is not None

    def test_group_member_missing_group_id_fails(self):
        """Test GroupMember validation fails without group_id."""
        with pytest.raises(ValidationError):
            GroupMember(user_id="user_123", added_at=datetime.utcnow())

    def test_group_member_missing_user_id_fails(self):
        """Test GroupMember validation fails without user_id."""
        with pytest.raises(ValidationError):
            GroupMember(group_id="group_abc123", added_at=datetime.utcnow())
