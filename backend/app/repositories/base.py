"""Base repository implementation for DynamoDB operations."""
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel
import inspect

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """Generic base repository for DynamoDB CRUD operations.

    Provides common database operations with automatic timestamp management.
    All operations follow immutable patterns, returning new objects.

    Type Parameters:
        T: Pydantic model type for the entity

    Attributes:
        table_name: DynamoDB table name
        pk_name: Primary key attribute name
        model: Pydantic model class for type conversion
    """

    def __init__(self, table_name: str, pk_name: str, model: type[T]) -> None:
        """Initialize repository with table configuration.

        Args:
            table_name: DynamoDB table name
            pk_name: Primary key attribute name (e.g., 'userId', 'datasetId')
            model: Pydantic model class
        """
        self.table_name = table_name
        self.pk_name = pk_name
        self.model = model

    def _to_dynamodb_item(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert Python dict to DynamoDB item format.

        Converts snake_case to camelCase and handles special conversions.

        Args:
            data: Python dictionary with snake_case keys

        Returns:
            DynamoDB item with camelCase keys
        """
        dynamodb_item = {}

        for key, value in data.items():
            # Convert snake_case to camelCase
            if key == 'id':
                # Map 'id' to the primary key name
                camel_key = self.pk_name
            else:
                camel_key = self._to_camel_case(key)

            # Handle timestamps: convert datetime to UNIX timestamp (Number)
            if isinstance(value, datetime):
                dynamodb_item[camel_key] = int(value.timestamp())
            # Handle nested dicts (e.g., DashboardLayout)
            elif isinstance(value, dict):
                dynamodb_item[camel_key] = self._convert_dict_to_camel_case(value)
            # Handle nested lists (e.g., layout items)
            elif isinstance(value, list) and value:
                if isinstance(value[0], BaseModel):
                    dynamodb_item[camel_key] = [
                        {self._to_camel_case(k): v for k, v in item.model_dump().items()}
                        for item in value
                    ]
                elif isinstance(value[0], dict):
                    dynamodb_item[camel_key] = [
                        self._convert_dict_to_camel_case(item)
                        for item in value
                    ]
                else:
                    dynamodb_item[camel_key] = value
            else:
                dynamodb_item[camel_key] = value

        return dynamodb_item

    def _from_dynamodb_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Convert DynamoDB item to Python dict format.

        Converts camelCase to snake_case and handles special conversions.

        Args:
            item: DynamoDB item with camelCase keys

        Returns:
            Python dictionary with snake_case keys
        """
        python_dict = {}

        for key, value in item.items():
            # Convert primary key to 'id'
            if key == self.pk_name:
                python_key = 'id'
            else:
                python_key = self._to_snake_case(key)

            # Handle timestamps: convert UNIX timestamp to datetime
            if key in ('createdAt', 'updatedAt'):
                python_dict[python_key] = datetime.fromtimestamp(int(value), tz=timezone.utc)
            # Handle nested dicts (e.g., DashboardLayout)
            elif isinstance(value, dict):
                python_dict[python_key] = self._convert_dict_to_snake_case(value)
            # Handle nested lists of dicts
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                python_dict[python_key] = [
                    self._convert_dict_to_snake_case(nested_item)
                    for nested_item in value
                ]
            else:
                python_dict[python_key] = value

        return python_dict

    def _convert_dict_to_camel_case(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively convert dict keys from snake_case to camelCase.

        Args:
            data: Dictionary with snake_case keys

        Returns:
            Dictionary with camelCase keys
        """
        result = {}
        for key, value in data.items():
            camel_key = self._to_camel_case(key)
            if isinstance(value, dict):
                result[camel_key] = self._convert_dict_to_camel_case(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                result[camel_key] = [self._convert_dict_to_camel_case(item) for item in value]
            else:
                result[camel_key] = value
        return result

    def _convert_dict_to_snake_case(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively convert dict keys from camelCase to snake_case.

        Args:
            data: Dictionary with camelCase keys

        Returns:
            Dictionary with snake_case keys
        """
        result = {}
        for key, value in data.items():
            snake_key = self._to_snake_case(key)
            if isinstance(value, dict):
                result[snake_key] = self._convert_dict_to_snake_case(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                result[snake_key] = [self._convert_dict_to_snake_case(item) for item in value]
            else:
                result[snake_key] = value
        return result

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase.

        Args:
            snake_str: String in snake_case format

        Returns:
            String in camelCase format
        """
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    def _to_snake_case(self, camel_str: str) -> str:
        """Convert camelCase to snake_case.

        Args:
            camel_str: String in camelCase format

        Returns:
            String in snake_case format
        """
        result = []
        for i, char in enumerate(camel_str):
            if char.isupper() and i > 0:
                result.append('_')
                result.append(char.lower())
            else:
                result.append(char.lower())
        return ''.join(result)

    async def _execute_db_operation(self, operation: Any) -> Any:
        """Execute a DynamoDB operation, handling both sync (boto3) and async (aioboto3).

        Args:
            operation: DynamoDB operation result (may be dict or coroutine)

        Returns:
            Operation result
        """
        if inspect.iscoroutine(operation):
            return await operation
        return operation

    async def create(self, data: dict[str, Any], dynamodb: Any) -> T:
        """Create a new item with automatic timestamp setting.

        Args:
            data: Item data dictionary (snake_case keys)
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            Created item as Pydantic model instance
        """
        # Create new dict to maintain immutability
        item_data = {**data}

        # Add timestamps
        now = datetime.now(timezone.utc)
        item_data['created_at'] = now
        item_data['updated_at'] = now

        # Convert to DynamoDB format and save
        dynamodb_item = self._to_dynamodb_item(item_data)
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)
        await self._execute_db_operation(table.put_item(Item=dynamodb_item))

        # Return as Pydantic model
        return self.model(**item_data)

    async def get_by_id(self, item_id: str, dynamodb: Any) -> Optional[T]:
        """Retrieve an item by primary key.

        Args:
            item_id: Primary key value
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            Item as Pydantic model instance, or None if not found
        """
        table_result = dynamodb.Table(self.table_name)
        # Handle both boto3 (returns Table directly) and aioboto3 (returns coroutine)
        table = await self._execute_db_operation(table_result)
        response = await self._execute_db_operation(table.get_item(Key={self.pk_name: item_id}))

        item = response.get('Item')
        if not item or not isinstance(item, dict):
            return None

        # Convert from DynamoDB format to Python dict
        python_dict = self._from_dynamodb_item(item)
        return self.model(**python_dict)

    async def update(
        self,
        item_id: str,
        data: dict[str, Any],
        dynamodb: Any
    ) -> Optional[T]:
        """Update an existing item with automatic updatedAt timestamp.

        Args:
            item_id: Primary key value
            data: Fields to update (snake_case keys)
            dynamodb: DynamoDB resource from aioboto3

        Returns:
            Updated item as Pydantic model instance, or None if not found
        """
        # Check if item exists
        existing = await self.get_by_id(item_id, dynamodb)
        if not existing:
            return None

        # Create update data with immutability
        update_data = {**data}
        update_data['updated_at'] = datetime.now(timezone.utc)

        # Build UpdateExpression dynamically
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        for key, value in update_data.items():
            camel_key = self._to_camel_case(key)
            placeholder_name = f"#{camel_key}"
            placeholder_value = f":{camel_key}"

            update_expression_parts.append(f"{placeholder_name} = {placeholder_value}")
            expression_attribute_names[placeholder_name] = camel_key

            # Convert datetime to timestamp
            if isinstance(value, datetime):
                expression_attribute_values[placeholder_value] = int(value.timestamp())
            # Handle nested dicts (e.g., DashboardLayout)
            elif isinstance(value, dict):
                expression_attribute_values[placeholder_value] = self._convert_dict_to_camel_case(value)
            # Handle nested lists
            elif isinstance(value, list) and value:
                if isinstance(value[0], BaseModel):
                    expression_attribute_values[placeholder_value] = [
                        {self._to_camel_case(k): v for k, v in item.model_dump().items()}
                        for item in value
                    ]
                elif isinstance(value[0], dict):
                    expression_attribute_values[placeholder_value] = [
                        self._convert_dict_to_camel_case(item)
                        for item in value
                    ]
                else:
                    expression_attribute_values[placeholder_value] = value
            else:
                expression_attribute_values[placeholder_value] = value

        update_expression = "SET " + ", ".join(update_expression_parts)

        # Execute update
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)
        response = await self._execute_db_operation(
            table.update_item(
                Key={self.pk_name: item_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
        )

        # Convert and return updated item
        updated_item = response.get('Attributes')
        if not updated_item or not isinstance(updated_item, dict):
            return None

        python_dict = self._from_dynamodb_item(updated_item)
        return self.model(**python_dict)

    async def delete(self, item_id: str, dynamodb: Any) -> None:
        """Delete an item by primary key.

        Args:
            item_id: Primary key value
            dynamodb: DynamoDB resource from aioboto3
        """
        table_result = dynamodb.Table(self.table_name)
        table = await self._execute_db_operation(table_result)
        await self._execute_db_operation(table.delete_item(Key={self.pk_name: item_id}))
