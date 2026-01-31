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

        Returns:
            Created Dataset instance
        """
        now = datetime.now(timezone.utc)

        dataset_data = {
            'id': dataset_id,
            'name': name,
            'description': None,
            'source_type': 'csv',
            'row_count': len(df),
            'schema': [col.model_dump() for col in schema],
            'owner_id': owner_id,
            's3_path': storage_result.s3_path,
            'partition_column': partition_column,
            'source_config': None,
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
