"""Schema comparison service for detecting schema changes between dataset versions."""
from app.models.dataset import ColumnSchema
from app.models.schema_change import SchemaChange, SchemaChangeType, SchemaCompareResult

# Re-export for convenience
__all__ = [
    "SchemaChange",
    "SchemaChangeType",
    "SchemaCompareResult",
    "compare_schemas",
]


def compare_schemas(
    old_schema: list[ColumnSchema],
    new_schema: list[ColumnSchema],
) -> SchemaCompareResult:
    """Compare two schemas and detect changes.

    Args:
        old_schema: The original schema (list of ColumnSchema).
        new_schema: The new schema to compare against (list of ColumnSchema).

    Returns:
        SchemaCompareResult containing has_changes flag and list of changes.
    """
    changes: list[SchemaChange] = []

    # Create mappings by column name
    old_by_name = {col.name: col for col in old_schema}
    new_by_name = {col.name: col for col in new_schema}

    # Detect removed columns (in old but not in new)
    for col_name, old_col in old_by_name.items():
        if col_name not in new_by_name:
            changes.append(
                SchemaChange(
                    column_name=col_name,
                    change_type=SchemaChangeType.REMOVED,
                    old_value=old_col.data_type,
                    new_value=None,
                )
            )

    # Detect added columns (in new but not in old)
    for col_name, new_col in new_by_name.items():
        if col_name not in old_by_name:
            changes.append(
                SchemaChange(
                    column_name=col_name,
                    change_type=SchemaChangeType.ADDED,
                    old_value=None,
                    new_value=new_col.data_type,
                )
            )

    # Detect changes in existing columns
    for col_name in old_by_name:
        if col_name in new_by_name:
            old_col = old_by_name[col_name]
            new_col = new_by_name[col_name]

            # Check data_type change
            if old_col.data_type != new_col.data_type:
                changes.append(
                    SchemaChange(
                        column_name=col_name,
                        change_type=SchemaChangeType.TYPE_CHANGED,
                        old_value=old_col.data_type,
                        new_value=new_col.data_type,
                    )
                )
            # Check nullable change (only if type didn't change)
            elif old_col.nullable != new_col.nullable:
                changes.append(
                    SchemaChange(
                        column_name=col_name,
                        change_type=SchemaChangeType.NULLABLE_CHANGED,
                        old_value=str(old_col.nullable),
                        new_value=str(new_col.nullable),
                    )
                )

    return SchemaCompareResult(
        has_changes=len(changes) > 0,
        changes=changes,
    )
