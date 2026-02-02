"""Group models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.common import TimestampMixin


class Group(TimestampMixin):
    """Group model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class GroupCreate(BaseModel):
    """Group creation request model."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v


class GroupUpdate(BaseModel):
    """Group update request model."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v


class GroupMember(BaseModel):
    """Group member model."""

    model_config = ConfigDict(from_attributes=True)

    group_id: str
    user_id: str
    added_at: datetime
