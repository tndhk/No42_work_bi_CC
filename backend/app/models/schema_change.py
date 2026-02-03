"""Schema change detection models."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SchemaChangeType(str, Enum):
    """Enum for types of schema changes."""

    ADDED = "added"
    REMOVED = "removed"
    TYPE_CHANGED = "type_changed"
    NULLABLE_CHANGED = "nullable_changed"


class SchemaChange(BaseModel):
    """Represents a single schema change for a column."""

    model_config = ConfigDict(from_attributes=True)

    column_name: str
    change_type: SchemaChangeType
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class SchemaCompareResult(BaseModel):
    """Result of comparing two schemas."""

    model_config = ConfigDict(from_attributes=True)

    has_changes: bool
    changes: list[SchemaChange]
