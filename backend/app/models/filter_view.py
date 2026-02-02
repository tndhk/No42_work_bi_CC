"""FilterView models."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.common import TimestampMixin


class FilterViewCreate(BaseModel):
    """FilterView creation request model."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1)
    filter_state: dict[str, Any]
    is_shared: bool = False
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v


class FilterViewUpdate(BaseModel):
    """FilterView update request model."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1)
    filter_state: Optional[dict[str, Any]] = None
    is_shared: Optional[bool] = None
    is_default: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v


class FilterView(TimestampMixin, BaseModel):
    """FilterView model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    dashboard_id: str
    name: str
    owner_id: str
    filter_state: dict[str, Any]
    is_shared: bool = False
    is_default: bool = False
    created_at: datetime
    updated_at: datetime
