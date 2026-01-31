"""Tests for Dataset models."""
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.models.dataset import Dataset, DatasetCreate, DatasetUpdate, ColumnSchema


class TestColumnSchema:
    """Test ColumnSchema model."""

    def test_column_schema_valid(self):
        """Test creating ColumnSchema with valid data."""
        column = ColumnSchema(
            name="age",
            data_type="int64",
            nullable=False
        )

        assert column.name == "age"
        assert column.data_type == "int64"
        assert column.nullable is False

    def test_column_schema_with_description(self):
        """Test ColumnSchema with description."""
        column = ColumnSchema(
            name="email",
            data_type="string",
            nullable=False,
            description="User email address"
        )

        assert column.description == "User email address"

    def test_column_schema_missing_name(self):
        """Test ColumnSchema validation fails without name."""
        with pytest.raises(ValidationError):
            ColumnSchema(
                data_type="int64",
                nullable=False
            )

    def test_column_schema_missing_data_type(self):
        """Test ColumnSchema validation fails without data_type."""
        with pytest.raises(ValidationError):
            ColumnSchema(
                name="age",
                nullable=False
            )


class TestDatasetCreate:
    """Test DatasetCreate model."""

    def test_dataset_create_valid(self):
        """Test creating DatasetCreate with valid data."""
        dataset = DatasetCreate(
            name="sales_data",
            description="Monthly sales records",
            source_type="csv"
        )

        assert dataset.name == "sales_data"
        assert dataset.description == "Monthly sales records"
        assert dataset.source_type == "csv"

    def test_dataset_create_missing_name(self):
        """Test DatasetCreate validation fails without name."""
        with pytest.raises(ValidationError):
            DatasetCreate(
                description="Test",
                source_type="csv"
            )

    def test_dataset_create_empty_name(self):
        """Test DatasetCreate validation fails with empty name."""
        with pytest.raises(ValidationError):
            DatasetCreate(
                name="",
                description="Test",
                source_type="csv"
            )

    def test_dataset_create_missing_source_type(self):
        """Test DatasetCreate validation fails without source_type."""
        with pytest.raises(ValidationError):
            DatasetCreate(
                name="sales_data",
                description="Test"
            )

    def test_dataset_create_optional_description(self):
        """Test DatasetCreate with optional description."""
        dataset = DatasetCreate(
            name="sales_data",
            source_type="csv"
        )

        assert dataset.description is None


class TestDataset:
    """Test Dataset model."""

    def test_dataset_valid(self):
        """Test creating Dataset with valid data."""
        now = datetime.utcnow()
        column = ColumnSchema(name="id", data_type="string", nullable=False)

        dataset = Dataset(
            id="dataset-123",
            name="sales_data",
            description="Sales records",
            source_type="csv",
            row_count=1000,
            schema=[column],
            created_at=now,
            updated_at=now
        )

        assert dataset.id == "dataset-123"
        assert dataset.name == "sales_data"
        assert dataset.row_count == 1000
        assert len(dataset.columns) == 1

    def test_dataset_missing_id(self):
        """Test Dataset validation fails without id."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Dataset(
                name="sales_data",
                source_type="csv",
                row_count=1000,
                schema=[],
                created_at=now,
                updated_at=now
            )

    def test_dataset_missing_schema(self):
        """Test Dataset validation fails without schema."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Dataset(
                id="dataset-123",
                name="sales_data",
                source_type="csv",
                row_count=1000,
                columns=[],
                created_at=now,
                updated_at=now
            )

        # Also test with missing columns field
        with pytest.raises(ValidationError):
            Dataset(
                id="dataset-123",
                name="sales_data",
                source_type="csv",
                row_count=1000,
                created_at=now,
                updated_at=now
            )

    def test_dataset_serialization(self):
        """Test Dataset serialization to dict."""
        now = datetime.utcnow()
        column = ColumnSchema(name="id", data_type="string", nullable=False)
        dataset = Dataset(
            id="dataset-123",
            name="sales_data",
            source_type="csv",
            row_count=1000,
            schema=[column],
            created_at=now,
            updated_at=now
        )

        dataset_dict = dataset.model_dump()
        assert dataset_dict["id"] == "dataset-123"
        assert dataset_dict["name"] == "sales_data"
        assert "columns" in dataset_dict


class TestDatasetUpdate:
    """Test DatasetUpdate model."""

    def test_dataset_update_valid(self):
        """Test creating DatasetUpdate with valid data."""
        update = DatasetUpdate(
            name="updated_sales",
            description="Updated description"
        )

        assert update.name == "updated_sales"
        assert update.description == "Updated description"

    def test_dataset_update_optional_fields(self):
        """Test DatasetUpdate with optional fields."""
        update = DatasetUpdate()

        assert update.name is None
        assert update.description is None

    def test_dataset_update_partial(self):
        """Test DatasetUpdate with partial fields."""
        update = DatasetUpdate(name="new_name")

        assert update.name == "new_name"
        assert update.description is None

    def test_dataset_update_empty_name(self):
        """Test DatasetUpdate validation fails with empty name."""
        with pytest.raises(ValidationError):
            DatasetUpdate(name="")

    def test_dataset_update_with_partition_column(self):
        """Test DatasetUpdate with partition_column."""
        update = DatasetUpdate(
            name="updated_sales",
            partition_column="date"
        )

        assert update.name == "updated_sales"
        assert update.partition_column == "date"


class TestDatasetExtendedFields:
    """Test Dataset extended fields for Phase 2."""

    def test_dataset_with_owner_id(self):
        """Test Dataset with owner_id field."""
        now = datetime.utcnow()
        column = ColumnSchema(name="id", data_type="string", nullable=False)

        dataset = Dataset(
            id="dataset-123",
            name="sales_data",
            source_type="csv",
            row_count=1000,
            schema=[column],
            owner_id="user-456",
            created_at=now,
            updated_at=now
        )

        assert dataset.owner_id == "user-456"

    def test_dataset_with_s3_path(self):
        """Test Dataset with s3_path field."""
        now = datetime.utcnow()
        column = ColumnSchema(name="id", data_type="string", nullable=False)

        dataset = Dataset(
            id="dataset-123",
            name="sales_data",
            source_type="csv",
            row_count=1000,
            schema=[column],
            s3_path="datasets/dataset-123/data/part-0000.parquet",
            created_at=now,
            updated_at=now
        )

        assert dataset.s3_path == "datasets/dataset-123/data/part-0000.parquet"

    def test_dataset_with_partition_column(self):
        """Test Dataset with partition_column field."""
        now = datetime.utcnow()
        column = ColumnSchema(name="id", data_type="string", nullable=False)

        dataset = Dataset(
            id="dataset-123",
            name="sales_data",
            source_type="csv",
            row_count=1000,
            schema=[column],
            partition_column="date",
            created_at=now,
            updated_at=now
        )

        assert dataset.partition_column == "date"

    def test_dataset_with_source_config(self):
        """Test Dataset with source_config field."""
        now = datetime.utcnow()
        column = ColumnSchema(name="id", data_type="string", nullable=False)
        source_config = {
            "encoding": "utf-8",
            "delimiter": ",",
            "has_header": True
        }

        dataset = Dataset(
            id="dataset-123",
            name="sales_data",
            source_type="csv",
            row_count=1000,
            schema=[column],
            source_config=source_config,
            created_at=now,
            updated_at=now
        )

        assert dataset.source_config == source_config
        assert dataset.source_config["encoding"] == "utf-8"

    def test_dataset_with_column_count(self):
        """Test Dataset with column_count field."""
        now = datetime.utcnow()
        column1 = ColumnSchema(name="id", data_type="string", nullable=False)
        column2 = ColumnSchema(name="name", data_type="string", nullable=False)

        dataset = Dataset(
            id="dataset-123",
            name="sales_data",
            source_type="csv",
            row_count=1000,
            schema=[column1, column2],
            column_count=2,
            created_at=now,
            updated_at=now
        )

        assert dataset.column_count == 2

    def test_dataset_with_import_timestamps(self):
        """Test Dataset with last_import_at and last_import_by fields."""
        now = datetime.utcnow()
        import_time = datetime(2024, 1, 15, 10, 30, 0)
        column = ColumnSchema(name="id", data_type="string", nullable=False)

        dataset = Dataset(
            id="dataset-123",
            name="sales_data",
            source_type="csv",
            row_count=1000,
            schema=[column],
            last_import_at=import_time,
            last_import_by="user-789",
            created_at=now,
            updated_at=now
        )

        assert dataset.last_import_at == import_time
        assert dataset.last_import_by == "user-789"

    def test_dataset_create_with_partition_column(self):
        """Test DatasetCreate with partition_column field."""
        dataset_create = DatasetCreate(
            name="sales_data",
            source_type="csv",
            partition_column="date"
        )

        assert dataset_create.partition_column == "date"
