"""Card models."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.common import TimestampMixin


class CardCreate(BaseModel):
    """Card creation request model."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    description: Optional[str] = None
    dataset_ids: Optional[list[str]] = None
    dataset_id: Optional[str] = None
    params: Optional[dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate code is not empty."""
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        return v


class CardUpdate(BaseModel):
    """Card update request model."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1)
    code: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    dataset_ids: Optional[list[str]] = None
    dataset_id: Optional[str] = None
    params: Optional[dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate code is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Code cannot be empty")
        return v


class Card(TimestampMixin, BaseModel):
    """Card model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    description: Optional[str] = None
    dataset_ids: Optional[list[str]] = None
    dataset_id: Optional[str] = None
    params: Optional[dict[str, Any]] = None
    used_columns: Optional[list[str]] = None
    filter_applicable: Optional[bool] = None
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
