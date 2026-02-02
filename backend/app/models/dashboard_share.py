"""DashboardShare models."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict


class Permission(str, Enum):
    """Permission levels for dashboard sharing."""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class SharedToType(str, Enum):
    """Target type for dashboard sharing."""
    USER = "user"
    GROUP = "group"


class DashboardShare(BaseModel):
    """Dashboard share model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    dashboard_id: str
    shared_to_type: SharedToType
    shared_to_id: str
    permission: Permission
    shared_by: str
    created_at: datetime


class DashboardShareCreate(BaseModel):
    """Dashboard share creation request model."""

    model_config = ConfigDict(from_attributes=True)

    shared_to_type: SharedToType
    shared_to_id: str
    permission: Permission


class DashboardShareUpdate(BaseModel):
    """Dashboard share update request model."""

    model_config = ConfigDict(from_attributes=True)

    permission: Permission
