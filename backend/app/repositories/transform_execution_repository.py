"""Transform execution repository for DynamoDB operations."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from app.core.config import settings
from app.models.transform_execution import TransformExecution
from app.repositories.base import BaseRepository


class TransformExecutionRepository(BaseRepository[TransformExecution]):
    """Repository for TransformExecution with composite key (transformId + startedAt)."""

    def __init__(self) -> None:
        super().__init__(
            table_name=f"{settings.dynamodb_table_prefix}transform_executions",
            pk_name='transformId',
            model=TransformExecution,
        )

    @staticmethod
    def _convert_for_dynamodb(value: Any) -> Any:
        """Convert a Python value to DynamoDB-compatible type."""
        if isinstance(value, datetime):
            return int(value.timestamp())
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    async def create(self, data: dict[str, Any], dynamodb: Any) -> TransformExecution:
        """Create execution record (no auto-timestamp - uses started_at instead)."""
        dynamodb_item = {}
        for key, value in data.items():
            camel_key = self._to_camel_case(key)
            dynamodb_item[camel_key] = self._convert_for_dynamodb(value)
        table = await self._execute_db_operation(dynamodb.Table(self.table_name))
        await self._execute_db_operation(table.put_item(Item=dynamodb_item))
        return self.model(**data)

    async def update_status(
        self,
        transform_id: str,
        started_at: datetime,
        updates: dict[str, Any],
        dynamodb: Any,
    ) -> None:
        """Update execution status by composite key."""
        update_parts = []
        attr_names = {}
        attr_values = {}
        for key, value in updates.items():
            camel = self._to_camel_case(key)
            update_parts.append(f"#{camel} = :{camel}")
            attr_names[f"#{camel}"] = camel
            attr_values[f":{camel}"] = self._convert_for_dynamodb(value)
        table = await self._execute_db_operation(dynamodb.Table(self.table_name))
        await self._execute_db_operation(
            table.update_item(
                Key={
                    'transformId': transform_id,
                    'startedAt': int(started_at.timestamp()),
                },
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeNames=attr_names,
                ExpressionAttributeValues=attr_values,
            )
        )

    async def list_by_transform(
        self,
        transform_id: str,
        dynamodb: Any,
        limit: int = 20,
    ) -> list[TransformExecution]:
        """List executions for a transform, newest first."""
        table = await self._execute_db_operation(dynamodb.Table(self.table_name))
        response = await self._execute_db_operation(
            table.query(
                KeyConditionExpression='transformId = :tid',
                ExpressionAttributeValues={':tid': transform_id},
                ScanIndexForward=False,
                Limit=limit,
            )
        )
        items = response.get('Items', [])
        return [self.model(**self._from_dynamodb_item(item)) for item in items]

    async def has_running_execution(
        self,
        transform_id: str,
        dynamodb: Any,
    ) -> bool:
        """Check if transform has a running execution."""
        executions = await self.list_by_transform(transform_id, dynamodb, limit=5)
        return any(e.status == "running" for e in executions)

    def _from_dynamodb_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Override to handle startedAt/finishedAt timestamp conversion and Decimal."""
        python_dict = {}
        timestamp_keys = {'startedAt', 'finishedAt'}
        for key, value in item.items():
            python_key = self._to_snake_case(key)
            if key in timestamp_keys and value is not None:
                python_dict[python_key] = datetime.fromtimestamp(int(value), tz=timezone.utc)
            elif isinstance(value, Decimal):
                # Convert Decimal back to int or float
                if value == int(value):
                    python_dict[python_key] = int(value)
                else:
                    python_dict[python_key] = float(value)
            else:
                python_dict[python_key] = value
        return python_dict
