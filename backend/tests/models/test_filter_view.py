"""Tests for FilterView models."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.models.filter_view import FilterView, FilterViewCreate, FilterViewUpdate


class TestFilterViewCreate:
    """Tests for FilterViewCreate model."""

    def test_valid_minimal(self):
        """Test creating FilterViewCreate with required fields only."""
        fv = FilterViewCreate(
            name="My View",
            filter_state={"category": "sales"},
        )
        assert fv.name == "My View"
        assert fv.filter_state == {"category": "sales"}
        assert fv.is_shared is False
        assert fv.is_default is False

    def test_valid_all_fields(self):
        """Test creating FilterViewCreate with all fields."""
        fv = FilterViewCreate(
            name="Shared View",
            filter_state={"category": "sales", "date_range": ["2024-01", "2024-12"]},
            is_shared=True,
            is_default=True,
        )
        assert fv.name == "Shared View"
        assert fv.is_shared is True
        assert fv.is_default is True

    def test_empty_name_fails(self):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError):
            FilterViewCreate(name="", filter_state={"a": 1})

    def test_whitespace_name_fails(self):
        """Test that whitespace-only name raises ValidationError."""
        with pytest.raises(ValidationError):
            FilterViewCreate(name="   ", filter_state={"a": 1})

    def test_missing_name_fails(self):
        """Test that missing name raises ValidationError."""
        with pytest.raises(ValidationError):
            FilterViewCreate(filter_state={"a": 1})

    def test_missing_filter_state_fails(self):
        """Test that missing filter_state raises ValidationError."""
        with pytest.raises(ValidationError):
            FilterViewCreate(name="Test")


class TestFilterViewUpdate:
    """Tests for FilterViewUpdate model."""

    def test_all_optional(self):
        """Test that all fields are optional."""
        fv = FilterViewUpdate()
        assert fv.name is None
        assert fv.filter_state is None
        assert fv.is_shared is None
        assert fv.is_default is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        fv = FilterViewUpdate(name="New Name", is_shared=True)
        assert fv.name == "New Name"
        assert fv.is_shared is True
        assert fv.filter_state is None

    def test_empty_name_fails(self):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError):
            FilterViewUpdate(name="")

    def test_whitespace_name_fails(self):
        """Test that whitespace-only name raises ValidationError."""
        with pytest.raises(ValidationError):
            FilterViewUpdate(name="   ")


class TestFilterView:
    """Tests for FilterView model."""

    def test_full_model(self):
        """Test creating full FilterView model."""
        now = datetime.now(timezone.utc)
        fv = FilterView(
            id="fv_abc123",
            dashboard_id="dashboard_xyz",
            name="Test View",
            owner_id="user_123",
            filter_state={"category": "sales"},
            is_shared=False,
            is_default=False,
            created_at=now,
            updated_at=now,
        )
        assert fv.id == "fv_abc123"
        assert fv.dashboard_id == "dashboard_xyz"
        assert fv.name == "Test View"
        assert fv.owner_id == "user_123"
        assert fv.filter_state == {"category": "sales"}
        assert fv.is_shared is False
        assert fv.is_default is False
        assert fv.created_at == now
        assert fv.updated_at == now

    def test_defaults(self):
        """Test FilterView default values."""
        now = datetime.now(timezone.utc)
        fv = FilterView(
            id="fv_abc123",
            dashboard_id="dashboard_xyz",
            name="Test",
            owner_id="user_123",
            filter_state={},
            created_at=now,
            updated_at=now,
        )
        assert fv.is_shared is False
        assert fv.is_default is False

    def test_missing_id_fails(self):
        """Test that missing id raises ValidationError."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            FilterView(
                dashboard_id="dashboard_xyz",
                name="Test",
                owner_id="user_123",
                filter_state={},
                created_at=now,
                updated_at=now,
            )

    def test_missing_dashboard_id_fails(self):
        """Test that missing dashboard_id raises ValidationError."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            FilterView(
                id="fv_abc123",
                name="Test",
                owner_id="user_123",
                filter_state={},
                created_at=now,
                updated_at=now,
            )

    def test_serialization(self):
        """Test FilterView serialization to dict."""
        now = datetime.now(timezone.utc)
        fv = FilterView(
            id="fv_abc123",
            dashboard_id="dashboard_xyz",
            name="Test View",
            owner_id="user_123",
            filter_state={"category": "sales"},
            created_at=now,
            updated_at=now,
        )
        fv_dict = fv.model_dump()
        assert fv_dict["id"] == "fv_abc123"
        assert fv_dict["dashboard_id"] == "dashboard_xyz"
        assert fv_dict["name"] == "Test View"
        assert fv_dict["filter_state"] == {"category": "sales"}
        assert fv_dict["is_shared"] is False
        assert fv_dict["is_default"] is False
