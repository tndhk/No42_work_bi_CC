"""Dashboard models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.common import TimestampMixin


class FilterDefinition(BaseModel):
    """Filter definition for dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    column: str
    label: str
    multi_select: bool = False


class LayoutItem(BaseModel):
    """Layout item for dashboard grid."""

    model_config = ConfigDict(from_attributes=True)

    card_id: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(ge=1)
    h: int = Field(ge=1)


class DashboardCreate(BaseModel):
    """Dashboard creation request model."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1)
    description: Optional[str] = None
    layout: Optional[list[LayoutItem]] = None
    filters: Optional[list[FilterDefinition]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v


class DashboardUpdate(BaseModel):
    """Dashboard update request model."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    layout: Optional[list[LayoutItem]] = None
    filters: Optional[list[FilterDefinition]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v


class Dashboard(TimestampMixin, BaseModel):
    """Dashboard model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    layout: Optional[list[LayoutItem]] = None
    owner_id: Optional[str] = None
    filters: Optional[list[FilterDefinition]] = None
    default_filter_view_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
