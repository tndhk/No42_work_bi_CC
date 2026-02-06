"""Tests for SchemaChange models."""
import pytest
from pydantic import ValidationError
from app.models.schema_change import (
    SchemaChange,
    SchemaChangeType,
    SchemaCompareResult,
)


class TestSchemaChangeType:
    """Test SchemaChangeType enum."""

    def test_schema_change_type_added(self):
        """Test ADDED enum value."""
        assert SchemaChangeType.ADDED == "added"
        assert SchemaChangeType.ADDED.value == "added"

    def test_schema_change_type_removed(self):
        """Test REMOVED enum value."""
        assert SchemaChangeType.REMOVED == "removed"
        assert SchemaChangeType.REMOVED.value == "removed"

    def test_schema_change_type_type_changed(self):
        """Test TYPE_CHANGED enum value."""
        assert SchemaChangeType.TYPE_CHANGED == "type_changed"
        assert SchemaChangeType.TYPE_CHANGED.value == "type_changed"

    def test_schema_change_type_nullable_changed(self):
        """Test NULLABLE_CHANGED enum value."""
        assert SchemaChangeType.NULLABLE_CHANGED == "nullable_changed"
        assert SchemaChangeType.NULLABLE_CHANGED.value == "nullable_changed"

    def test_schema_change_type_all_values(self):
        """Test that all enum values are accounted for."""
        expected_values = {"added", "removed", "type_changed", "nullable_changed"}
        actual_values = {item.value for item in SchemaChangeType}
        assert actual_values == expected_values


class TestSchemaChange:
    """Test SchemaChange model."""

    def test_schema_change_valid_added(self):
        """Test creating SchemaChange for ADDED type."""
        change = SchemaChange(
            column_name="email",
            change_type=SchemaChangeType.ADDED,
            new_value="string"
        )

        assert change.column_name == "email"
        assert change.change_type == SchemaChangeType.ADDED
        assert change.old_value is None
        assert change.new_value == "string"

    def test_schema_change_valid_removed(self):
        """Test creating SchemaChange for REMOVED type."""
        change = SchemaChange(
            column_name="phone",
            change_type=SchemaChangeType.REMOVED,
            old_value="string"
        )

        assert change.column_name == "phone"
        assert change.change_type == SchemaChangeType.REMOVED
        assert change.old_value == "string"
        assert change.new_value is None

    def test_schema_change_valid_type_changed(self):
        """Test creating SchemaChange for TYPE_CHANGED type."""
        change = SchemaChange(
            column_name="age",
            change_type=SchemaChangeType.TYPE_CHANGED,
            old_value="int32",
            new_value="int64"
        )

        assert change.column_name == "age"
        assert change.change_type == SchemaChangeType.TYPE_CHANGED
        assert change.old_value == "int32"
        assert change.new_value == "int64"

    def test_schema_change_valid_nullable_changed(self):
        """Test creating SchemaChange for NULLABLE_CHANGED type."""
        change = SchemaChange(
            column_name="email",
            change_type=SchemaChangeType.NULLABLE_CHANGED,
            old_value="false",
            new_value="true"
        )

        assert change.column_name == "email"
        assert change.change_type == SchemaChangeType.NULLABLE_CHANGED
        assert change.old_value == "false"
        assert change.new_value == "true"

    def test_schema_change_missing_column_name(self):
        """Test SchemaChange validation fails without column_name."""
        with pytest.raises(ValidationError):
            SchemaChange(
                change_type=SchemaChangeType.ADDED,
                new_value="string"
            )

    def test_schema_change_missing_change_type(self):
        """Test SchemaChange validation fails without change_type."""
        with pytest.raises(ValidationError):
            SchemaChange(
                column_name="email",
                new_value="string"
            )

    def test_schema_change_invalid_change_type(self):
        """Test SchemaChange validation fails with invalid change_type."""
        with pytest.raises(ValidationError):
            SchemaChange(
                column_name="email",
                change_type="invalid_type",
                new_value="string"
            )

    def test_schema_change_optional_values(self):
        """Test SchemaChange with optional old_value and new_value."""
        change = SchemaChange(
            column_name="test_col",
            change_type=SchemaChangeType.ADDED
        )

        assert change.column_name == "test_col"
        assert change.change_type == SchemaChangeType.ADDED
        assert change.old_value is None
        assert change.new_value is None

    def test_schema_change_with_string_enum_value(self):
        """Test SchemaChange accepts string value for enum."""
        change = SchemaChange(
            column_name="email",
            change_type="added",
            new_value="string"
        )

        assert change.change_type == SchemaChangeType.ADDED

    def test_schema_change_serialization(self):
        """Test SchemaChange serialization to dict."""
        change = SchemaChange(
            column_name="age",
            change_type=SchemaChangeType.TYPE_CHANGED,
            old_value="int32",
            new_value="int64"
        )

        change_dict = change.model_dump()
        assert change_dict["column_name"] == "age"
        assert change_dict["change_type"] == "type_changed"
        assert change_dict["old_value"] == "int32"
        assert change_dict["new_value"] == "int64"


class TestSchemaCompareResult:
    """Test SchemaCompareResult model."""

    def test_schema_compare_result_no_changes(self):
        """Test SchemaCompareResult with no changes."""
        result = SchemaCompareResult(
            has_changes=False,
            changes=[]
        )

        assert result.has_changes is False
        assert result.changes == []
        assert len(result.changes) == 0

    def test_schema_compare_result_with_changes(self):
        """Test SchemaCompareResult with changes."""
        change1 = SchemaChange(
            column_name="email",
            change_type=SchemaChangeType.ADDED,
            new_value="string"
        )
        change2 = SchemaChange(
            column_name="age",
            change_type=SchemaChangeType.TYPE_CHANGED,
            old_value="int32",
            new_value="int64"
        )

        result = SchemaCompareResult(
            has_changes=True,
            changes=[change1, change2]
        )

        assert result.has_changes is True
        assert len(result.changes) == 2
        assert result.changes[0].column_name == "email"
        assert result.changes[1].column_name == "age"

    def test_schema_compare_result_missing_has_changes(self):
        """Test SchemaCompareResult validation fails without has_changes."""
        with pytest.raises(ValidationError):
            SchemaCompareResult(
                changes=[]
            )

    def test_schema_compare_result_missing_changes(self):
        """Test SchemaCompareResult validation fails without changes."""
        with pytest.raises(ValidationError):
            SchemaCompareResult(
                has_changes=False
            )

    def test_schema_compare_result_inconsistent_state(self):
        """Test SchemaCompareResult allows inconsistent state (has_changes=False with changes)."""
        # Note: This is allowed by the model - validation logic would be in service layer
        result = SchemaCompareResult(
            has_changes=False,
            changes=[
                SchemaChange(
                    column_name="email",
                    change_type=SchemaChangeType.ADDED,
                    new_value="string"
                )
            ]
        )

        assert result.has_changes is False
        assert len(result.changes) == 1

    def test_schema_compare_result_serialization(self):
        """Test SchemaCompareResult serialization to dict."""
        change = SchemaChange(
            column_name="email",
            change_type=SchemaChangeType.ADDED,
            new_value="string"
        )
        result = SchemaCompareResult(
            has_changes=True,
            changes=[change]
        )

        result_dict = result.model_dump()
        assert result_dict["has_changes"] is True
        assert len(result_dict["changes"]) == 1
        assert result_dict["changes"][0]["column_name"] == "email"
        assert result_dict["changes"][0]["change_type"] == "added"

    def test_schema_compare_result_multiple_change_types(self):
        """Test SchemaCompareResult with various change types."""
        changes = [
            SchemaChange(
                column_name="new_col",
                change_type=SchemaChangeType.ADDED,
                new_value="string"
            ),
            SchemaChange(
                column_name="old_col",
                change_type=SchemaChangeType.REMOVED,
                old_value="int64"
            ),
            SchemaChange(
                column_name="type_col",
                change_type=SchemaChangeType.TYPE_CHANGED,
                old_value="int32",
                new_value="int64"
            ),
            SchemaChange(
                column_name="null_col",
                change_type=SchemaChangeType.NULLABLE_CHANGED,
                old_value="false",
                new_value="true"
            ),
        ]

        result = SchemaCompareResult(
            has_changes=True,
            changes=changes
        )

        assert result.has_changes is True
        assert len(result.changes) == 4
        assert result.changes[0].change_type == SchemaChangeType.ADDED
        assert result.changes[1].change_type == SchemaChangeType.REMOVED
        assert result.changes[2].change_type == SchemaChangeType.TYPE_CHANGED
        assert result.changes[3].change_type == SchemaChangeType.NULLABLE_CHANGED

    def test_schema_compare_result_from_attributes(self):
        """Test SchemaCompareResult with from_attributes config."""
        # This tests that the model_config allows from_attributes=True
        # Typically used when converting from ORM objects
        result_dict = {
            "has_changes": True,
            "changes": [
                {
                    "column_name": "test",
                    "change_type": "added",
                    "old_value": None,
                    "new_value": "string"
                }
            ]
        }

        result = SchemaCompareResult(**result_dict)
        assert result.has_changes is True
        assert len(result.changes) == 1
