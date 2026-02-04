"""Audit log models."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class EventType(str, Enum):
    """Audit log event types."""
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    DASHBOARD_SHARE_ADDED = "DASHBOARD_SHARE_ADDED"
    DASHBOARD_SHARE_REMOVED = "DASHBOARD_SHARE_REMOVED"
    DASHBOARD_SHARE_UPDATED = "DASHBOARD_SHARE_UPDATED"
    DATASET_CREATED = "DATASET_CREATED"
    DATASET_IMPORTED = "DATASET_IMPORTED"
    DATASET_DELETED = "DATASET_DELETED"
    TRANSFORM_EXECUTED = "TRANSFORM_EXECUTED"
    TRANSFORM_FAILED = "TRANSFORM_FAILED"
    CARD_EXECUTION_FAILED = "CARD_EXECUTION_FAILED"


class AuditLog(BaseModel):
    """Audit log entry."""
    model_config = ConfigDict(from_attributes=True)

    log_id: str
    timestamp: datetime
    event_type: EventType
    user_id: str
    target_type: str
    target_id: str
    details: dict = {}
    request_id: Optional[str] = None
