"""Audit log repository for DynamoDB operations."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from app.core.config import settings
from app.models.audit_log import AuditLog, EventType
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog with composite key (logId + timestamp)."""

    def __init__(self) -> None:
        super().__init__(
            table_name=f"{settings.dynamodb_table_prefix}audit_logs",
            pk_name='logId',
            model=AuditLog,
        )

    @staticmethod
    def _convert_for_dynamodb(value: Any) -> Any:
        """Convert a Python value to DynamoDB-compatible type."""
        if isinstance(value, datetime):
            return int(value.timestamp())
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    async def create(self, data: dict[str, Any], dynamodb: Any) -> AuditLog:
        """Create audit log record (no auto-timestamp management)."""
        dynamodb_item = {}
        for key, value in data.items():
            camel_key = self._to_camel_case(key)
            dynamodb_item[camel_key] = self._convert_for_dynamodb(value)
        table = await self._execute_db_operation(dynamodb.Table(self.table_name))
        await self._execute_db_operation(table.put_item(Item=dynamodb_item))
        # Convert event_type string back to enum for model construction
        model_data = {**data}
        if isinstance(model_data.get('event_type'), str):
            model_data['event_type'] = EventType(model_data['event_type'])
        return self.model(**model_data)

    async def list_all(
        self,
        dynamodb: Any,
        event_type: Optional[EventType] = None,
        user_id: Optional[str] = None,
        target_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[AuditLog]:
        """List all audit logs with optional filters (Scan + FilterExpression)."""
        # If user_id or target_id is specified, delegate to GSI-based methods
        # and apply remaining filters in memory
        if target_id:
            items = await self.list_by_target(target_id, dynamodb, start_date=start_date, end_date=end_date)
            if event_type:
                items = [i for i in items if i.event_type == event_type]
            if user_id:
                items = [i for i in items if i.user_id == user_id]
            return items
        if user_id:
            items = await self.list_by_user(user_id, dynamodb, start_date=start_date, end_date=end_date)
            if event_type:
                items = [i for i in items if i.event_type == event_type]
            return items

        table = await self._execute_db_operation(dynamodb.Table(self.table_name))

        # Build filter expression
        filter_parts = []
        attr_values = {}
        attr_names = {}

        if event_type:
            filter_parts.append("#et = :et")
            attr_names["#et"] = "eventType"
            attr_values[":et"] = event_type.value

        if start_date:
            filter_parts.append("#ts >= :start")
            attr_names["#ts"] = "timestamp"
            attr_values[":start"] = int(start_date.timestamp())

        if end_date:
            if "#ts" not in attr_names:
                attr_names["#ts"] = "timestamp"
            filter_parts.append("#ts <= :end")
            attr_values[":end"] = int(end_date.timestamp())

        scan_kwargs: dict[str, Any] = {}
        if filter_parts:
            scan_kwargs["FilterExpression"] = " AND ".join(filter_parts)
            scan_kwargs["ExpressionAttributeNames"] = attr_names
            scan_kwargs["ExpressionAttributeValues"] = attr_values

        response = await self._execute_db_operation(table.scan(**scan_kwargs))
        items = response.get("Items", [])
        # Sort newest first
        items.sort(key=lambda x: int(x.get("timestamp", 0)), reverse=True)
        return [self.model(**self._from_dynamodb_item(item)) for item in items]

    async def list_by_user(
        self,
        user_id: str,
        dynamodb: Any,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[AuditLog]:
        """List logs by user ID using LogsByUser GSI, newest first."""
        table = await self._execute_db_operation(dynamodb.Table(self.table_name))

        key_expr = "userId = :uid"
        attr_values: dict[str, Any] = {":uid": user_id}

        if start_date and end_date:
            key_expr += " AND #ts BETWEEN :start AND :end"
            attr_values[":start"] = int(start_date.timestamp())
            attr_values[":end"] = int(end_date.timestamp())
        elif start_date:
            key_expr += " AND #ts >= :start"
            attr_values[":start"] = int(start_date.timestamp())
        elif end_date:
            key_expr += " AND #ts <= :end"
            attr_values[":end"] = int(end_date.timestamp())

        query_kwargs: dict[str, Any] = {
            "IndexName": "LogsByUser",
            "KeyConditionExpression": key_expr,
            "ExpressionAttributeValues": attr_values,
            "ScanIndexForward": False,
        }
        if start_date or end_date:
            query_kwargs["ExpressionAttributeNames"] = {"#ts": "timestamp"}

        response = await self._execute_db_operation(table.query(**query_kwargs))
        items = response.get("Items", [])
        return [self.model(**self._from_dynamodb_item(item)) for item in items]

    async def list_by_target(
        self,
        target_id: str,
        dynamodb: Any,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[AuditLog]:
        """List logs by target ID using LogsByTarget GSI, newest first."""
        table = await self._execute_db_operation(dynamodb.Table(self.table_name))

        key_expr = "targetId = :tid"
        attr_values: dict[str, Any] = {":tid": target_id}

        if start_date and end_date:
            key_expr += " AND #ts BETWEEN :start AND :end"
            attr_values[":start"] = int(start_date.timestamp())
            attr_values[":end"] = int(end_date.timestamp())
        elif start_date:
            key_expr += " AND #ts >= :start"
            attr_values[":start"] = int(start_date.timestamp())
        elif end_date:
            key_expr += " AND #ts <= :end"
            attr_values[":end"] = int(end_date.timestamp())

        query_kwargs: dict[str, Any] = {
            "IndexName": "LogsByTarget",
            "KeyConditionExpression": key_expr,
            "ExpressionAttributeValues": attr_values,
            "ScanIndexForward": False,
        }
        if start_date or end_date:
            query_kwargs["ExpressionAttributeNames"] = {"#ts": "timestamp"}

        response = await self._execute_db_operation(table.query(**query_kwargs))
        items = response.get("Items", [])
        return [self.model(**self._from_dynamodb_item(item)) for item in items]

    def _from_dynamodb_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Override to handle timestamp conversion and Decimal."""
        python_dict = {}
        for key, value in item.items():
            python_key = self._to_snake_case(key)
            if key == 'logId':
                python_dict['log_id'] = value
            elif key == 'timestamp' and value is not None:
                python_dict['timestamp'] = datetime.fromtimestamp(int(value), tz=timezone.utc)
            elif isinstance(value, Decimal):
                if value == int(value):
                    python_dict[python_key] = int(value)
                else:
                    python_dict[python_key] = float(value)
            else:
                python_dict[python_key] = value
        return python_dict
