"""Dataset service for CSV import and preview operations."""
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.core.config import settings
from app.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.services.csv_parser import CsvImportOptions, parse_full
from app.services.parquet_storage import ParquetConverter, ParquetReader
from app.services.schema_comparator import compare_schemas
from app.services.type_inferrer import infer_schema


class DatasetService:
    """Service for dataset operations including CSV import and preview."""

    async def import_csv(
        self,
        file_bytes: bytes,
        name: str,
        owner_id: str,
        dynamodb: Any,
        s3_client: Any,
        encoding: str | None = None,
        delimiter: str = ",",
        partition_column: str | None = None,
    ) -> Dataset:
        """Import CSV file and save as Parquet to S3 with metadata in DynamoDB.

        Args:
            file_bytes: Raw CSV file bytes
            name: Dataset name
            owner_id: Owner user ID
            dynamodb: DynamoDB resource
            s3_client: S3 client
            encoding: Optional encoding (auto-detected if None)
            delimiter: Column delimiter (default: comma)
            partition_column: Optional column to partition by

        Returns:
            Created Dataset instance

        Raises:
            ValueError: If inputs are invalid or CSV is empty
        """
        # Validate inputs
        self._validate_import_inputs(file_bytes, name, owner_id)

        # Generate dataset ID
        dataset_id = self._generate_dataset_id()

        # Parse CSV
        csv_options = self._build_csv_options(encoding, delimiter)
        df = parse_full(file_bytes, csv_options)

        if df.empty:
            raise ValueError("CSV file is empty or could not be parsed")

        # Infer schema
        schema = infer_schema(df)

        # Convert and save to S3
        storage_result = self._save_to_s3(
            df, dataset_id, s3_client, partition_column
        )

        # Save metadata to DynamoDB
        dataset = await self._save_metadata(
            dataset_id=dataset_id,
            name=name,
            owner_id=owner_id,
            df=df,
            schema=schema,
            storage_result=storage_result,
            partition_column=partition_column,
            dynamodb=dynamodb,
        )

        return dataset

    async def import_s3_csv(
        self,
        name: str,
        s3_bucket: str,
        s3_key: str,
        owner_id: str,
        dynamodb: Any,
        s3_client: Any,
        source_s3_client: Any,
        has_header: bool = True,
        encoding: str | None = None,
        delimiter: str = ",",
        partition_column: str | None = None,
    ) -> Dataset:
        """Import CSV file from S3 and save as Parquet.

        Args:
            name: Dataset name
            s3_bucket: Source S3 bucket name
            s3_key: Source S3 object key
            owner_id: Owner user ID
            dynamodb: DynamoDB resource
            s3_client: S3 client for Parquet storage
            source_s3_client: S3 client for source CSV retrieval
            has_header: Whether CSV has header row
            encoding: Optional encoding (auto-detected if None)
            delimiter: Column delimiter (default: comma)
            partition_column: Optional column to partition by

        Returns:
            Created Dataset instance

        Raises:
            ValueError: If inputs are invalid, S3 key not found, or CSV is empty
        """
        # Validate inputs
        if not name or not name.strip():
            raise ValueError("name cannot be empty")
        if not owner_id or not owner_id.strip():
            raise ValueError("owner_id cannot be empty")

        # Fetch CSV from S3
        try:
            response = await source_s3_client.get_object(
                Bucket=s3_bucket, Key=s3_key
            )
            file_bytes = await response["Body"].read()
        except Exception as e:
            error_str = str(e)
            if "NoSuchKey" in error_str or "Not Found" in error_str or "404" in error_str:
                raise ValueError(f"S3 object not found: s3://{s3_bucket}/{s3_key}")
            raise ValueError(f"S3 error retrieving s3://{s3_bucket}/{s3_key}: {error_str}")

        if not file_bytes:
            raise ValueError("S3 CSV file is empty")

        # Generate dataset ID
        dataset_id = self._generate_dataset_id()

        # Parse CSV
        csv_options = self._build_csv_options(encoding, delimiter)
        df = parse_full(file_bytes, csv_options)

        if df.empty:
            raise ValueError("CSV file is empty or could not be parsed")

        # Infer schema
        schema = infer_schema(df)

        # Convert and save to S3
        storage_result = self._save_to_s3(
            df, dataset_id, s3_client, partition_column
        )

        # Save metadata to DynamoDB with S3 source config
        dataset = await self._save_metadata(
            dataset_id=dataset_id,
            name=name.strip(),
            owner_id=owner_id,
            df=df,
            schema=schema,
            storage_result=storage_result,
            partition_column=partition_column,
            dynamodb=dynamodb,
            source_type='s3_csv',
            source_config={
                's3_bucket': s3_bucket,
                's3_key': s3_key,
            },
        )

        return dataset

    async def get_column_values(
        self,
        dataset: Dataset,
        column_name: str,
        s3_client: Any,
        max_values: int = 500,
    ) -> list[str]:
        """Get unique values for a specific column from a dataset.

        Args:
            dataset: Dataset instance
            column_name: Column name to get values for
            s3_client: S3 client
            max_values: Maximum number of unique values to return

        Returns:
            Sorted list of unique string values

        Raises:
            ValueError: If column doesn't exist or dataset has no data
        """
        if not dataset.s3_path:
            raise ValueError("Dataset has no data")

        reader = ParquetReader(
            s3_client=s3_client,
            bucket=settings.s3_bucket_datasets,
        )
        df = reader.read_full(dataset.s3_path)

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in dataset")

        values = df[column_name].dropna().unique()
        str_values = sorted([str(v) for v in values])

        return str_values[:max_values]

    async def get_preview(
        self,
        dataset: Dataset,
        s3_client: Any,
        max_rows: int = 100,
    ) -> dict[str, Any]:
        """Get preview of dataset from S3.

        Args:
            dataset: Dataset instance
            s3_client: S3 client
            max_rows: Maximum rows to return (1-1000)

        Returns:
            Preview dictionary with columns, rows, total_rows, preview_rows

        Raises:
            ValueError: If max_rows is out of range
        """
        # Validate max_rows
        if max_rows < 1 or max_rows > 1000:
            raise ValueError("max_rows must be between 1 and 1000")

        # Return empty if no S3 path
        if not dataset.s3_path:
            return {
                'columns': [],
                'rows': [],
                'total_rows': 0,
                'preview_rows': 0,
            }

        # Read from S3
        df = self._read_from_s3(dataset.s3_path, s3_client, max_rows)

        # Convert to preview format
        return self._format_preview(df, dataset.row_count)

    def _validate_import_inputs(
        self,
        file_bytes: bytes,
        name: str,
        owner_id: str,
    ) -> None:
        """Validate import_csv inputs.

        Args:
            file_bytes: CSV bytes
            name: Dataset name
            owner_id: Owner ID

        Raises:
            ValueError: If any input is invalid
        """
        if not file_bytes:
            raise ValueError("CSV file is empty")

        if not name or not name.strip():
            raise ValueError("name cannot be empty")

        if not owner_id or not owner_id.strip():
            raise ValueError("owner_id cannot be empty")

    def _generate_dataset_id(self) -> str:
        """Generate dataset ID with ds_ prefix.

        Returns:
            Dataset ID (e.g., ds_a1b2c3d4e5f6)
        """
        return f"ds_{uuid.uuid4().hex[:12]}"

    def _build_csv_options(
        self,
        encoding: str | None,
        delimiter: str,
    ) -> CsvImportOptions:
        """Build CSV import options.

        Args:
            encoding: Optional encoding
            delimiter: Delimiter character

        Returns:
            CsvImportOptions instance
        """
        return CsvImportOptions(
            encoding=encoding,
            delimiter=delimiter,
            has_header=True,
        )

    def _save_to_s3(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        s3_client: Any,
        partition_column: str | None,
    ) -> Any:
        """Save DataFrame to S3 as Parquet.

        Args:
            df: DataFrame to save
            dataset_id: Dataset ID
            s3_client: S3 client
            partition_column: Optional partition column

        Returns:
            StorageResult from ParquetConverter
        """
        converter = ParquetConverter(
            s3_client=s3_client,
            bucket=settings.s3_bucket_datasets,
        )

        return converter.convert_and_save(
            df=df,
            dataset_id=dataset_id,
            partition_column=partition_column,
        )

    async def _save_metadata(
        self,
        dataset_id: str,
        name: str,
        owner_id: str,
        df: pd.DataFrame,
        schema: list[Any],
        storage_result: Any,
        partition_column: str | None,
        dynamodb: Any,
        source_type: str = 'csv',
        source_config: dict[str, Any] | None = None,
    ) -> Dataset:
        """Save dataset metadata to DynamoDB.

        Args:
            dataset_id: Dataset ID
            name: Dataset name
            owner_id: Owner user ID
            df: DataFrame (for row/column counts)
            schema: Column schema list
            storage_result: S3 storage result
            partition_column: Optional partition column
            dynamodb: DynamoDB resource
            source_type: Source type identifier (default: 'csv')
            source_config: Optional source configuration dict

        Returns:
            Created Dataset instance
        """
        now = datetime.now(timezone.utc)

        dataset_data = {
            'id': dataset_id,
            'name': name,
            'description': None,
            'source_type': source_type,
            'row_count': len(df),
            'schema': [col.model_dump() for col in schema],
            'owner_id': owner_id,
            's3_path': storage_result.s3_path,
            'partition_column': partition_column,
            'source_config': source_config,
            'column_count': len(df.columns),
            'last_import_at': now,
            'last_import_by': owner_id,
        }

        repo = DatasetRepository()
        dataset = await repo.create(dataset_data, dynamodb)

        return dataset

    def _read_from_s3(
        self,
        s3_path: str,
        s3_client: Any,
        max_rows: int,
    ) -> pd.DataFrame:
        """Read Parquet data from S3.

        Args:
            s3_path: S3 path
            s3_client: S3 client
            max_rows: Maximum rows to read

        Returns:
            DataFrame with preview data
        """
        reader = ParquetReader(
            s3_client=s3_client,
            bucket=settings.s3_bucket_datasets,
        )

        return reader.read_preview(s3_path, max_rows)

    def _format_preview(
        self,
        df: pd.DataFrame,
        total_rows: int,
    ) -> dict[str, Any]:
        """Format DataFrame as preview dictionary.

        Args:
            df: DataFrame to format
            total_rows: Total rows in full dataset

        Returns:
            Preview dictionary
        """
        return {
            'columns': df.columns.tolist(),
            'rows': df.to_dict('records'),
            'total_rows': total_rows,
            'preview_rows': len(df),
        }

    async def reimport_dry_run(
        self,
        dataset_id: str,
        user_id: str,
        dynamodb: Any,
        s3_client: Any,
        source_s3_client: Any,
    ) -> dict[str, Any]:
        """Perform a dry run of reimport to check for schema changes.

        Args:
            dataset_id: Dataset ID to reimport
            user_id: User performing the reimport
            dynamodb: DynamoDB resource
            s3_client: S3 client for Parquet storage
            source_s3_client: S3 client for source CSV retrieval

        Returns:
            Dictionary with:
                - has_schema_changes: bool
                - changes: list of SchemaChange
                - new_row_count: int
                - new_column_count: int

        Raises:
            ValueError: If dataset not found, not s3_csv type, or S3 file not found
        """
        # Get dataset from DynamoDB
        repo = DatasetRepository()
        dataset = await repo.get_by_id(dataset_id, dynamodb)

        if not dataset:
            raise ValueError("Dataset not found")

        # Check source type
        if dataset.source_type != 's3_csv':
            raise ValueError("Reimport is only supported for s3_csv datasets")

        # Get source config
        source_config = dataset.source_config or {}
        s3_bucket = source_config.get('s3_bucket')
        s3_key = source_config.get('s3_key')

        # Fetch CSV from S3
        file_bytes = await self._fetch_s3_csv(
            source_s3_client, s3_bucket, s3_key
        )

        # Parse CSV and infer schema
        csv_options = self._build_csv_options(
            source_config.get('encoding'),
            source_config.get('delimiter', ','),
        )
        df = parse_full(file_bytes, csv_options)
        new_schema = infer_schema(df)

        # Compare schemas
        old_schema = dataset.columns or []
        compare_result = compare_schemas(old_schema, new_schema)

        return {
            'has_schema_changes': compare_result.has_changes,
            'changes': compare_result.changes,
            'new_row_count': len(df),
            'new_column_count': len(df.columns),
        }

    async def reimport_execute(
        self,
        dataset_id: str,
        user_id: str,
        dynamodb: Any,
        s3_client: Any,
        source_s3_client: Any,
        force: bool = False,
    ) -> Dataset:
        """Execute reimport of a dataset from its S3 source.

        Args:
            dataset_id: Dataset ID to reimport
            user_id: User performing the reimport
            dynamodb: DynamoDB resource
            s3_client: S3 client for Parquet storage
            source_s3_client: S3 client for source CSV retrieval
            force: If True, proceed even with schema changes

        Returns:
            Updated Dataset instance

        Raises:
            ValueError: If dataset not found, not s3_csv type, S3 file not found,
                        or schema changes detected without force=True
        """
        # Get dataset from DynamoDB
        repo = DatasetRepository()
        dataset = await repo.get_by_id(dataset_id, dynamodb)

        if not dataset:
            raise ValueError("Dataset not found")

        # Check source type
        if dataset.source_type != 's3_csv':
            raise ValueError("Reimport is only supported for s3_csv datasets")

        # Get source config
        source_config = dataset.source_config or {}
        s3_bucket = source_config.get('s3_bucket')
        s3_key = source_config.get('s3_key')

        # Fetch CSV from S3
        file_bytes = await self._fetch_s3_csv(
            source_s3_client, s3_bucket, s3_key
        )

        # Parse CSV and infer schema
        csv_options = self._build_csv_options(
            source_config.get('encoding'),
            source_config.get('delimiter', ','),
        )
        df = parse_full(file_bytes, csv_options)
        new_schema = infer_schema(df)

        # Compare schemas
        old_schema = dataset.columns or []
        compare_result = compare_schemas(old_schema, new_schema)

        # Check for schema changes
        if compare_result.has_changes and not force:
            raise ValueError("Schema changes detected. Use force=True to proceed.")

        # Save to S3 (overwrite existing path)
        storage_result = self._save_to_s3(
            df, dataset_id, s3_client, dataset.partition_column
        )

        # Update metadata in DynamoDB (full overwrite via put_item)
        now = datetime.now(timezone.utc)
        updated_data = {
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'source_type': dataset.source_type,
            'row_count': len(df),
            'column_count': len(df.columns),
            'schema': [col.model_dump() for col in new_schema],
            'owner_id': dataset.owner_id,
            's3_path': storage_result.s3_path,
            'partition_column': dataset.partition_column,
            'source_config': dataset.source_config,
            'last_import_at': now,
            'last_import_by': user_id,
            'created_at': dataset.created_at,
            'updated_at': now,
        }

        updated_dataset = await repo.create(updated_data, dynamodb)
        return updated_dataset

    async def _fetch_s3_csv(
        self,
        source_s3_client: Any,
        s3_bucket: str,
        s3_key: str,
    ) -> bytes:
        """Fetch CSV file from S3.

        Args:
            source_s3_client: S3 client for source bucket
            s3_bucket: S3 bucket name
            s3_key: S3 object key

        Returns:
            CSV file bytes

        Raises:
            ValueError: If S3 file not found
        """
        try:
            response = source_s3_client.get_object(
                Bucket=s3_bucket, Key=s3_key
            )
            body = response['Body']
            # Handle both sync and async read
            read_result = body.read()
            if hasattr(read_result, '__await__'):
                return await read_result
            return read_result
        except Exception as e:
            error_str = str(e)
            if 'NoSuchKey' in error_str or 'Not Found' in error_str or '404' in error_str:
                raise ValueError(f"S3 file not found: s3://{s3_bucket}/{s3_key}")
            raise ValueError(f"S3 error retrieving s3://{s3_bucket}/{s3_key}: {error_str}")
