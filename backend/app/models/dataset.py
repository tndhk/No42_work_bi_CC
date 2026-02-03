"""Dataset models."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.common import TimestampMixin
from app.models.schema_change import SchemaChange


class ColumnSchema(BaseModel):
    """Schema definition for a dataset column."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    data_type: str
    nullable: bool = False
    description: Optional[str] = None


class DatasetCreate(BaseModel):
    """Dataset creation request model."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1)
    description: Optional[str] = None
    source_type: str
    partition_column: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v


class DatasetUpdate(BaseModel):
    """Dataset update request model."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    partition_column: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v


class S3ImportRequest(BaseModel):
    """S3 CSV import request model."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1)
    s3_bucket: str = Field(min_length=1)
    s3_key: str = Field(min_length=1)
    has_header: bool = True
    delimiter: str = ","
    encoding: Optional[str] = None
    partition_column: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v


class Dataset(TimestampMixin, BaseModel):
    """Dataset model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    source_type: str
    row_count: int = 0
    columns: list[ColumnSchema] = Field(alias="schema")
    owner_id: Optional[str] = None
    s3_path: Optional[str] = None
    partition_column: Optional[str] = None
    source_config: Optional[dict[str, Any]] = None
    column_count: int = 0
    last_import_at: Optional[datetime] = None
    last_import_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReimportDryRunResponse(BaseModel):
    """Response model for reimport dry-run."""

    model_config = ConfigDict(from_attributes=True)

    has_schema_changes: bool
    changes: list[SchemaChange]
    new_row_count: int
    new_column_count: int


class ReimportRequest(BaseModel):
    """Request model for reimport."""

    model_config = ConfigDict(from_attributes=True)

    force: bool = False
