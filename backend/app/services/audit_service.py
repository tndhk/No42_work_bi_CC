"""Audit logging service."""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.models.audit_log import AuditLog, EventType
from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    """Service for logging audit events."""

    async def log_event(
        self,
        event_type: EventType,
        user_id: str,
        target_type: str,
        target_id: str,
        dynamodb: Any,
        details: Optional[dict] = None,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log an audit event.

        Args:
            event_type: The type of event
            user_id: ID of the user performing the action
            target_type: Type of the target resource (e.g., "user", "dataset", "transform")
            target_id: ID of the target resource
            dynamodb: DynamoDB resource
            details: Optional additional details about the event
            request_id: Optional request ID for tracing

        Returns:
            The created AuditLog, or None if logging failed
        """
        try:
            log_id = f"log_{uuid.uuid4().hex[:12]}"
            timestamp = datetime.now(timezone.utc)

            repo = AuditLogRepository()
            log = await repo.create(
                {
                    "log_id": log_id,
                    "timestamp": timestamp,
                    "event_type": event_type.value,
                    "user_id": user_id,
                    "target_type": target_type,
                    "target_id": target_id,
                    "details": details or {},
                    "request_id": request_id,
                },
                dynamodb,
            )
            return log
        except Exception:
            # Do not propagate audit logging errors to preserve business logic
            return None

    async def log_user_login(
        self,
        user_id: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a successful user login event."""
        return await self.log_event(
            event_type=EventType.USER_LOGIN,
            user_id=user_id,
            target_type="user",
            target_id=user_id,
            dynamodb=dynamodb,
            request_id=request_id,
        )

    async def log_user_logout(
        self,
        user_id: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a user logout event."""
        return await self.log_event(
            event_type=EventType.USER_LOGOUT,
            user_id=user_id,
            target_type="user",
            target_id=user_id,
            dynamodb=dynamodb,
            request_id=request_id,
        )

    async def log_user_login_failed(
        self,
        email: str,
        reason: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a failed login attempt.

        Args:
            email: Email address that was used for login attempt
            reason: Reason for failure (e.g., "user_not_found", "invalid_password")
            dynamodb: DynamoDB resource
            request_id: Optional request ID
        """
        return await self.log_event(
            event_type=EventType.USER_LOGIN_FAILED,
            user_id="unknown",  # DynamoDB GSI keys cannot be empty strings
            target_type="email",
            target_id=email,
            dynamodb=dynamodb,
            details={"reason": reason},
            request_id=request_id,
        )

    async def log_dashboard_share_added(
        self,
        user_id: str,
        dashboard_id: str,
        shared_to_type: str,
        shared_to_id: str,
        permission: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a dashboard share creation event."""
        return await self.log_event(
            event_type=EventType.DASHBOARD_SHARE_ADDED,
            user_id=user_id,
            target_type="dashboard",
            target_id=dashboard_id,
            dynamodb=dynamodb,
            details={
                "shared_to_type": shared_to_type,
                "shared_to_id": shared_to_id,
                "permission": permission,
            },
            request_id=request_id,
        )

    async def log_dashboard_share_removed(
        self,
        user_id: str,
        dashboard_id: str,
        shared_to_type: str,
        shared_to_id: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a dashboard share removal event."""
        return await self.log_event(
            event_type=EventType.DASHBOARD_SHARE_REMOVED,
            user_id=user_id,
            target_type="dashboard",
            target_id=dashboard_id,
            dynamodb=dynamodb,
            details={
                "shared_to_type": shared_to_type,
                "shared_to_id": shared_to_id,
            },
            request_id=request_id,
        )

    async def log_dashboard_share_updated(
        self,
        user_id: str,
        dashboard_id: str,
        shared_to_type: str,
        shared_to_id: str,
        permission: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a dashboard share permission update event."""
        return await self.log_event(
            event_type=EventType.DASHBOARD_SHARE_UPDATED,
            user_id=user_id,
            target_type="dashboard",
            target_id=dashboard_id,
            dynamodb=dynamodb,
            details={
                "shared_to_type": shared_to_type,
                "shared_to_id": shared_to_id,
                "permission": permission,
            },
            request_id=request_id,
        )

    async def log_dataset_created(
        self,
        user_id: str,
        dataset_id: str,
        dataset_name: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a dataset creation event."""
        return await self.log_event(
            event_type=EventType.DATASET_CREATED,
            user_id=user_id,
            target_type="dataset",
            target_id=dataset_id,
            dynamodb=dynamodb,
            details={"name": dataset_name},
            request_id=request_id,
        )

    async def log_dataset_imported(
        self,
        user_id: str,
        dataset_id: str,
        dataset_name: str,
        source_type: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a dataset import event.

        Args:
            user_id: User performing the import
            dataset_id: ID of the dataset
            dataset_name: Name of the dataset
            source_type: Type of import source (e.g., "s3_csv", "reimport")
            dynamodb: DynamoDB resource
            request_id: Optional request ID
        """
        return await self.log_event(
            event_type=EventType.DATASET_IMPORTED,
            user_id=user_id,
            target_type="dataset",
            target_id=dataset_id,
            dynamodb=dynamodb,
            details={"name": dataset_name, "source_type": source_type},
            request_id=request_id,
        )

    async def log_dataset_deleted(
        self,
        user_id: str,
        dataset_id: str,
        dataset_name: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a dataset deletion event."""
        return await self.log_event(
            event_type=EventType.DATASET_DELETED,
            user_id=user_id,
            target_type="dataset",
            target_id=dataset_id,
            dynamodb=dynamodb,
            details={"name": dataset_name},
            request_id=request_id,
        )

    async def log_transform_executed(
        self,
        user_id: str,
        transform_id: str,
        execution_id: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a successful transform execution event."""
        return await self.log_event(
            event_type=EventType.TRANSFORM_EXECUTED,
            user_id=user_id,
            target_type="transform",
            target_id=transform_id,
            dynamodb=dynamodb,
            details={"execution_id": execution_id},
            request_id=request_id,
        )

    async def log_transform_failed(
        self,
        user_id: str,
        transform_id: str,
        error: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a failed transform execution event."""
        return await self.log_event(
            event_type=EventType.TRANSFORM_FAILED,
            user_id=user_id,
            target_type="transform",
            target_id=transform_id,
            dynamodb=dynamodb,
            details={"error": error},
            request_id=request_id,
        )

    async def log_card_execution_failed(
        self,
        user_id: str,
        card_id: str,
        error: str,
        dynamodb: Any,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Log a failed card execution event."""
        return await self.log_event(
            event_type=EventType.CARD_EXECUTION_FAILED,
            user_id=user_id,
            target_type="card",
            target_id=card_id,
            dynamodb=dynamodb,
            details={"error": error},
            request_id=request_id,
        )
