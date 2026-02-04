"""Transform models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.common import TimestampMixin


class TransformCreate(BaseModel):
    """Transform creation request model."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1)
    input_dataset_ids: list[str] = Field(min_length=1)
    code: str = Field(min_length=1)
    schedule_cron: Optional[str] = None
    schedule_enabled: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate code is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        return v

    @field_validator("schedule_cron")
    @classmethod
    def validate_schedule_cron(cls, v: Optional[str]) -> Optional[str]:
        """Validate cron expression is parseable."""
        if v is not None:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError(f"Invalid cron expression: {v}")
        return v


class TransformUpdate(BaseModel):
    """Transform update request model."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1)
    input_dataset_ids: Optional[list[str]] = Field(None, min_length=1)
    code: Optional[str] = Field(None, min_length=1)
    schedule_cron: Optional[str] = None
    schedule_enabled: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty or whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate code is not empty or whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Code cannot be empty")
        return v

    @field_validator("schedule_cron")
    @classmethod
    def validate_schedule_cron(cls, v: Optional[str]) -> Optional[str]:
        """Validate cron expression if provided."""
        if v is not None:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError(f"Invalid cron expression: {v}")
        return v


class Transform(TimestampMixin, BaseModel):
    """Transform model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    owner_id: str
    input_dataset_ids: list[str] = Field(min_length=1)
    output_dataset_id: Optional[str] = None
    code: str
    schedule_cron: Optional[str] = None
    schedule_enabled: bool = False
    created_at: datetime
    updated_at: datetime
