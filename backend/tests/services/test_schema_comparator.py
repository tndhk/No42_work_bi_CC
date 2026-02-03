"""Tests for schema_comparator module."""
import pytest

from app.models.dataset import ColumnSchema
from app.services.schema_comparator import (
    SchemaChange,
    SchemaChangeType,
    SchemaCompareResult,
    compare_schemas,
)


@pytest.fixture
def sample_schema() -> list[ColumnSchema]:
    """Create sample schema for testing."""
    return [
        ColumnSchema(name='id', data_type='int64', nullable=False),
        ColumnSchema(name='name', data_type='string', nullable=False),
        ColumnSchema(name='email', data_type='string', nullable=True),
        ColumnSchema(name='age', data_type='int64', nullable=True),
    ]


class TestSchemaComparator:
    """Tests for compare_schemas function."""

    def test_identical_schemas_returns_no_changes(
        self,
        sample_schema: list[ColumnSchema],
    ) -> None:
        """Test that identical schemas return has_changes=False and empty changes list."""
        # Arrange
        old_schema = sample_schema
        new_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
            ColumnSchema(name='email', data_type='string', nullable=True),
            ColumnSchema(name='age', data_type='int64', nullable=True),
        ]

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert isinstance(result, SchemaCompareResult)
        assert result.has_changes is False
        assert result.changes == []

    def test_detect_added_column(self) -> None:
        """Test detection of newly added column."""
        # Arrange
        old_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
        ]
        new_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
            ColumnSchema(name='email', data_type='string', nullable=True),
        ]

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is True
        assert len(result.changes) == 1

        change = result.changes[0]
        assert change.change_type == SchemaChangeType.ADDED
        assert change.column_name == 'email'
        assert change.old_value is None
        assert change.new_value == 'string'

    def test_detect_removed_column(self) -> None:
        """Test detection of removed column."""
        # Arrange
        old_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
            ColumnSchema(name='email', data_type='string', nullable=True),
        ]
        new_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
        ]

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is True
        assert len(result.changes) == 1

        change = result.changes[0]
        assert change.change_type == SchemaChangeType.REMOVED
        assert change.column_name == 'email'
        assert change.old_value == 'string'
        assert change.new_value is None

    def test_detect_type_changed(self) -> None:
        """Test detection of column type change."""
        # Arrange
        old_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='age', data_type='string', nullable=False),
        ]
        new_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='age', data_type='int64', nullable=False),
        ]

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is True
        assert len(result.changes) == 1

        change = result.changes[0]
        assert change.change_type == SchemaChangeType.TYPE_CHANGED
        assert change.column_name == 'age'
        assert change.old_value == 'string'
        assert change.new_value == 'int64'

    def test_detect_nullable_changed(self) -> None:
        """Test detection of nullable attribute change."""
        # Arrange
        old_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
        ]
        new_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=True),
        ]

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is True
        assert len(result.changes) == 1

        change = result.changes[0]
        assert change.change_type == SchemaChangeType.NULLABLE_CHANGED
        assert change.column_name == 'name'
        assert change.old_value == 'False'
        assert change.new_value == 'True'

    def test_detect_multiple_changes(self) -> None:
        """Test detection of multiple schema changes simultaneously."""
        # Arrange
        old_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
            ColumnSchema(name='old_column', data_type='string', nullable=True),
        ]
        new_schema = [
            ColumnSchema(name='id', data_type='string', nullable=False),  # type changed
            ColumnSchema(name='name', data_type='string', nullable=True),  # nullable changed
            ColumnSchema(name='new_column', data_type='int64', nullable=False),  # added
            # old_column removed
        ]

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is True
        assert len(result.changes) == 4

        # Verify each change type is present
        change_types = {c.change_type for c in result.changes}
        assert SchemaChangeType.ADDED in change_types
        assert SchemaChangeType.REMOVED in change_types
        assert SchemaChangeType.TYPE_CHANGED in change_types
        assert SchemaChangeType.NULLABLE_CHANGED in change_types

        # Verify specific changes
        changes_by_column = {c.column_name: c for c in result.changes}

        assert changes_by_column['id'].change_type == SchemaChangeType.TYPE_CHANGED
        assert changes_by_column['id'].old_value == 'int64'
        assert changes_by_column['id'].new_value == 'string'

        assert changes_by_column['name'].change_type == SchemaChangeType.NULLABLE_CHANGED
        assert changes_by_column['name'].old_value == 'False'
        assert changes_by_column['name'].new_value == 'True'

        assert changes_by_column['old_column'].change_type == SchemaChangeType.REMOVED
        assert changes_by_column['new_column'].change_type == SchemaChangeType.ADDED


class TestSchemaComparatorEdgeCases:
    """Edge case tests for compare_schemas function."""

    def test_empty_schemas_no_changes(self) -> None:
        """Test that two empty schemas return no changes."""
        # Arrange
        old_schema: list[ColumnSchema] = []
        new_schema: list[ColumnSchema] = []

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is False
        assert result.changes == []

    def test_old_empty_new_has_columns(self) -> None:
        """Test adding columns to an empty schema."""
        # Arrange
        old_schema: list[ColumnSchema] = []
        new_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
        ]

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is True
        assert len(result.changes) == 2
        assert all(c.change_type == SchemaChangeType.ADDED for c in result.changes)

    def test_new_empty_old_has_columns(self) -> None:
        """Test removing all columns from a schema."""
        # Arrange
        old_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
        ]
        new_schema: list[ColumnSchema] = []

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is True
        assert len(result.changes) == 2
        assert all(c.change_type == SchemaChangeType.REMOVED for c in result.changes)

    def test_column_order_does_not_matter(self) -> None:
        """Test that column order does not affect comparison."""
        # Arrange
        old_schema = [
            ColumnSchema(name='id', data_type='int64', nullable=False),
            ColumnSchema(name='name', data_type='string', nullable=False),
        ]
        new_schema = [
            ColumnSchema(name='name', data_type='string', nullable=False),
            ColumnSchema(name='id', data_type='int64', nullable=False),
        ]

        # Act
        result = compare_schemas(old_schema, new_schema)

        # Assert
        assert result.has_changes is False
        assert result.changes == []
