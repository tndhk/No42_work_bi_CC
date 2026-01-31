"""Common model components and base classes."""
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class BaseResponse(BaseModel):
    """Generic API response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class TimestampMixin(BaseModel):
    """Mixin to add created_at and updated_at timestamps to models."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
