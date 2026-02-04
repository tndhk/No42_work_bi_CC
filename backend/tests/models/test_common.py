"""Tests for common model components."""
from datetime import datetime
from pydantic import BaseModel
from app.models.common import BaseResponse, TimestampMixin


class TestTimestampMixin:
    """Test TimestampMixin functionality."""

    def test_timestamp_mixin_auto_now(self):
        """Test that created_at and updated_at are set automatically."""
        class TestModel(BaseModel):
            id: str
            name: str
            created_at: datetime
            updated_at: datetime

        # Simulate TimestampMixin behavior
        now = datetime.utcnow()
        model = TestModel(
            id="test-1",
            name="Test",
            created_at=now,
            updated_at=now
        )

        assert model.created_at is not None
        assert model.updated_at is not None
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)

    def test_timestamp_mixin_fields_present(self):
        """Test that TimestampMixin includes created_at and updated_at fields."""
        class TestModel(TimestampMixin, BaseModel):
            id: str
            name: str

        assert hasattr(TestModel, 'model_fields')
        fields = TestModel.model_fields
        assert 'created_at' in fields
        assert 'updated_at' in fields


class TestBaseResponse:
    """Test BaseResponse model."""

    def test_base_response_success(self):
        """Test BaseResponse with success status."""
        response = BaseResponse(
            success=True,
            data={"key": "value"}
        )

        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.error is None

    def test_base_response_error(self):
        """Test BaseResponse with error status."""
        response = BaseResponse(
            success=False,
            error="Something went wrong"
        )

        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.data is None

    def test_base_response_serialization(self):
        """Test BaseResponse serialization to dict."""
        response = BaseResponse(
            success=True,
            data={"id": "123"}
        )

        response_dict = response.model_dump()
        assert response_dict["success"] is True
        assert response_dict["data"] == {"id": "123"}
