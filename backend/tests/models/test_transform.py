"""Tests for Transform models."""
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.models.transform import Transform, TransformCreate, TransformUpdate


class TestTransformCreate:
    """Test TransformCreate model."""

    def test_transform_create_valid(self):
        """Test creating TransformCreate with valid data."""
        transform = TransformCreate(
            name="Sales Aggregation",
            input_dataset_ids=["dataset-1"],
            code="def transform(inputs, params):\n    return inputs[0]"
        )

        assert transform.name == "Sales Aggregation"
        assert transform.input_dataset_ids == ["dataset-1"]
        assert "def transform" in transform.code

    def test_transform_create_multiple_inputs(self):
        """Test TransformCreate with multiple input datasets."""
        transform = TransformCreate(
            name="Join Transform",
            input_dataset_ids=["dataset-1", "dataset-2", "dataset-3"],
            code="def transform(inputs, params):\n    return merged"
        )

        assert len(transform.input_dataset_ids) == 3

    def test_transform_create_missing_name(self):
        """Test TransformCreate validation fails without name."""
        with pytest.raises(ValidationError):
            TransformCreate(
                input_dataset_ids=["dataset-1"],
                code="def transform(inputs, params): pass"
            )

    def test_transform_create_empty_name(self):
        """Test TransformCreate validation fails with empty name."""
        with pytest.raises(ValidationError):
            TransformCreate(
                name="",
                input_dataset_ids=["dataset-1"],
                code="def transform(inputs, params): pass"
            )

    def test_transform_create_whitespace_name(self):
        """Test TransformCreate validation fails with whitespace-only name."""
        with pytest.raises(ValidationError):
            TransformCreate(
                name="   ",
                input_dataset_ids=["dataset-1"],
                code="def transform(inputs, params): pass"
            )

    def test_transform_create_missing_input_dataset_ids(self):
        """Test TransformCreate validation fails without input_dataset_ids."""
        with pytest.raises(ValidationError):
            TransformCreate(
                name="Transform",
                code="def transform(inputs, params): pass"
            )

    def test_transform_create_empty_input_dataset_ids(self):
        """Test TransformCreate validation fails with empty input_dataset_ids list."""
        with pytest.raises(ValidationError):
            TransformCreate(
                name="Transform",
                input_dataset_ids=[],
                code="def transform(inputs, params): pass"
            )

    def test_transform_create_missing_code(self):
        """Test TransformCreate validation fails without code."""
        with pytest.raises(ValidationError):
            TransformCreate(
                name="Transform",
                input_dataset_ids=["dataset-1"]
            )

    def test_transform_create_empty_code(self):
        """Test TransformCreate validation fails with empty code."""
        with pytest.raises(ValidationError):
            TransformCreate(
                name="Transform",
                input_dataset_ids=["dataset-1"],
                code=""
            )

    def test_transform_create_whitespace_code(self):
        """Test TransformCreate validation fails with whitespace-only code."""
        with pytest.raises(ValidationError):
            TransformCreate(
                name="Transform",
                input_dataset_ids=["dataset-1"],
                code="   "
            )


class TestTransform:
    """Test Transform model."""

    def test_transform_valid(self):
        """Test creating Transform with valid data."""
        now = datetime.utcnow()
        transform = Transform(
            id="transform-123",
            name="Sales Aggregation",
            owner_id="user-456",
            input_dataset_ids=["dataset-1"],
            code="def transform(inputs, params):\n    return inputs[0]",
            created_at=now,
            updated_at=now
        )

        assert transform.id == "transform-123"
        assert transform.name == "Sales Aggregation"
        assert transform.owner_id == "user-456"
        assert transform.input_dataset_ids == ["dataset-1"]
        assert transform.output_dataset_id is None

    def test_transform_with_output_dataset_id(self):
        """Test Transform with output_dataset_id."""
        now = datetime.utcnow()
        transform = Transform(
            id="transform-123",
            name="Sales Aggregation",
            owner_id="user-456",
            input_dataset_ids=["dataset-1"],
            output_dataset_id="dataset-output",
            code="def transform(inputs, params): pass",
            created_at=now,
            updated_at=now
        )

        assert transform.output_dataset_id == "dataset-output"

    def test_transform_with_multiple_inputs(self):
        """Test Transform with multiple input datasets."""
        now = datetime.utcnow()
        transform = Transform(
            id="transform-123",
            name="Join Transform",
            owner_id="user-456",
            input_dataset_ids=["dataset-1", "dataset-2"],
            code="def transform(inputs, params): pass",
            created_at=now,
            updated_at=now
        )

        assert len(transform.input_dataset_ids) == 2

    def test_transform_missing_id(self):
        """Test Transform validation fails without id."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Transform(
                name="Transform",
                owner_id="user-456",
                input_dataset_ids=["dataset-1"],
                code="def transform(inputs, params): pass",
                created_at=now,
                updated_at=now
            )

    def test_transform_missing_owner_id(self):
        """Test Transform validation fails without owner_id."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Transform(
                id="transform-123",
                name="Transform",
                input_dataset_ids=["dataset-1"],
                code="def transform(inputs, params): pass",
                created_at=now,
                updated_at=now
            )

    def test_transform_missing_input_dataset_ids(self):
        """Test Transform validation fails without input_dataset_ids."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Transform(
                id="transform-123",
                name="Transform",
                owner_id="user-456",
                code="def transform(inputs, params): pass",
                created_at=now,
                updated_at=now
            )

    def test_transform_empty_input_dataset_ids(self):
        """Test Transform validation fails with empty input_dataset_ids."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Transform(
                id="transform-123",
                name="Transform",
                owner_id="user-456",
                input_dataset_ids=[],
                code="def transform(inputs, params): pass",
                created_at=now,
                updated_at=now
            )

    def test_transform_serialization(self):
        """Test Transform serialization to dict."""
        now = datetime.utcnow()
        transform = Transform(
            id="transform-123",
            name="Sales Aggregation",
            owner_id="user-456",
            input_dataset_ids=["dataset-1", "dataset-2"],
            code="def transform(inputs, params): pass",
            created_at=now,
            updated_at=now
        )

        transform_dict = transform.model_dump()
        assert transform_dict["id"] == "transform-123"
        assert transform_dict["name"] == "Sales Aggregation"
        assert transform_dict["owner_id"] == "user-456"
        assert transform_dict["input_dataset_ids"] == ["dataset-1", "dataset-2"]
        assert transform_dict["output_dataset_id"] is None


class TestTransformUpdate:
    """Test TransformUpdate model."""

    def test_transform_update_valid(self):
        """Test creating TransformUpdate with valid data."""
        update = TransformUpdate(
            name="Updated Transform",
            code="def transform(inputs, params): return updated"
        )

        assert update.name == "Updated Transform"
        assert update.code == "def transform(inputs, params): return updated"

    def test_transform_update_optional_fields(self):
        """Test TransformUpdate with all fields optional."""
        update = TransformUpdate()

        assert update.name is None
        assert update.input_dataset_ids is None
        assert update.code is None

    def test_transform_update_partial_name_only(self):
        """Test TransformUpdate with only name."""
        update = TransformUpdate(name="New Name")

        assert update.name == "New Name"
        assert update.code is None
        assert update.input_dataset_ids is None

    def test_transform_update_partial_code_only(self):
        """Test TransformUpdate with only code."""
        update = TransformUpdate(code="def transform(inputs, params): return new")

        assert update.code == "def transform(inputs, params): return new"
        assert update.name is None

    def test_transform_update_partial_input_dataset_ids_only(self):
        """Test TransformUpdate with only input_dataset_ids."""
        update = TransformUpdate(
            input_dataset_ids=["dataset-new-1", "dataset-new-2"]
        )

        assert update.input_dataset_ids == ["dataset-new-1", "dataset-new-2"]
        assert update.name is None
        assert update.code is None

    def test_transform_update_empty_name(self):
        """Test TransformUpdate validation fails with empty name."""
        with pytest.raises(ValidationError):
            TransformUpdate(name="")

    def test_transform_update_whitespace_name(self):
        """Test TransformUpdate validation fails with whitespace-only name."""
        with pytest.raises(ValidationError):
            TransformUpdate(name="   ")

    def test_transform_update_empty_code(self):
        """Test TransformUpdate validation fails with empty code."""
        with pytest.raises(ValidationError):
            TransformUpdate(code="")

    def test_transform_update_whitespace_code(self):
        """Test TransformUpdate validation fails with whitespace-only code."""
        with pytest.raises(ValidationError):
            TransformUpdate(code="   ")

    def test_transform_update_empty_input_dataset_ids(self):
        """Test TransformUpdate validation fails with empty input_dataset_ids when provided."""
        with pytest.raises(ValidationError):
            TransformUpdate(input_dataset_ids=[])

    def test_transform_update_valid_input_dataset_ids(self):
        """Test TransformUpdate with valid input_dataset_ids."""
        update = TransformUpdate(
            input_dataset_ids=["dataset-1"]
        )

        assert update.input_dataset_ids == ["dataset-1"]


class TestTransformSchedule:
    """Test schedule_cron and schedule_enabled fields on Transform models."""

    def test_transform_with_schedule(self):
        """Test Transform with schedule_cron and schedule_enabled set."""
        now = datetime.utcnow()
        transform = Transform(
            id="transform-123",
            name="Scheduled Transform",
            owner_id="user-456",
            input_dataset_ids=["dataset-1"],
            code="def transform(inputs, params): pass",
            schedule_cron="0 0 * * *",
            schedule_enabled=True,
            created_at=now,
            updated_at=now,
        )

        assert transform.schedule_cron == "0 0 * * *"
        assert transform.schedule_enabled is True

    def test_transform_default_schedule_disabled(self):
        """Test Transform defaults: schedule_cron=None, schedule_enabled=False."""
        now = datetime.utcnow()
        transform = Transform(
            id="transform-123",
            name="Default Transform",
            owner_id="user-456",
            input_dataset_ids=["dataset-1"],
            code="def transform(inputs, params): pass",
            created_at=now,
            updated_at=now,
        )

        assert transform.schedule_cron is None
        assert transform.schedule_enabled is False

    def test_transform_create_with_valid_cron(self):
        """Test TransformCreate accepts a valid cron expression."""
        tc = TransformCreate(
            name="Cron Transform",
            input_dataset_ids=["dataset-1"],
            code="def transform(inputs, params): pass",
            schedule_cron="0 0 * * *",
            schedule_enabled=True,
        )

        assert tc.schedule_cron == "0 0 * * *"
        assert tc.schedule_enabled is True

    def test_transform_create_with_invalid_cron(self):
        """Test TransformCreate rejects an invalid cron expression with ValidationError."""
        with pytest.raises(ValidationError, match="Invalid cron expression"):
            TransformCreate(
                name="Bad Cron Transform",
                input_dataset_ids=["dataset-1"],
                code="def transform(inputs, params): pass",
                schedule_cron="invalid",
            )

    def test_transform_update_schedule(self):
        """Test TransformUpdate can update schedule_cron."""
        update = TransformUpdate(
            schedule_cron="30 2 * * 1",
            schedule_enabled=True,
        )

        assert update.schedule_cron == "30 2 * * 1"
        assert update.schedule_enabled is True
