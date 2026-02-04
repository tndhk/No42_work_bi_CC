"""Audit Logs API routes."""
from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_dynamodb_resource, require_admin
from app.api.response import paginated_response
from app.models.audit_log import EventType
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository

router = APIRouter()


@router.get("")
async def list_audit_logs(
    event_type: Optional[EventType] = Query(None),
    user_id: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> dict[str, Any]:
    """List audit logs with optional filters (admin only).

    Args:
        event_type: Filter by event type
        user_id: Filter by user ID
        target_id: Filter by target ID
        start_date: Filter by start date (ISO 8601)
        end_date: Filter by end date (ISO 8601)
        limit: Maximum number of items to return (1-100, default: 50)
        offset: Number of items to skip (default: 0)
        current_user: Authenticated admin user
        dynamodb: DynamoDB resource

    Returns:
        Paginated list of audit logs
    """
    repo = AuditLogRepository()
    all_logs = await repo.list_all(
        dynamodb,
        event_type=event_type,
        user_id=user_id,
        target_id=target_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Apply pagination
    total = len(all_logs)
    logs = all_logs[offset:offset + limit]

    return paginated_response(
        items=[log.model_dump() for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )
