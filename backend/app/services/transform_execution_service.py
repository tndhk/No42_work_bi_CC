"""Transform execution service for running transforms via Executor API."""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd

from app.core.config import settings
from app.models.dataset import ColumnSchema
from app.models.transform import Transform
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.transform_repository import TransformRepository
from app.services.parquet_storage import ParquetConverter, ParquetReader

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5  # seconds


@dataclass(frozen=True)
class TransformExecutionResult:
    """Immutable result from transform execution.

    Attributes:
        output_dataset_id: ID of the created output dataset
        row_count: Number of rows in the output
        column_names: List of column names in the output
        execution_time_ms: Total execution time in milliseconds
    """

    output_dataset_id: str
    row_count: int
    column_names: list[str]
    execution_time_ms: float


class TransformExecutionService:
    """Service for executing transforms via Executor API.

    This service orchestrates the complete transform execution flow:
    1. Load input datasets from S3
    2. Call Executor API to run the transform
    3. Save output as a new dataset
    4. Update the transform with the output dataset ID
    """

    async def execute(
        self,
        transform: Transform,
        dynamodb: Any,
        s3: Any,
    ) -> TransformExecutionResult:
        """Execute a transform and create output dataset.

        Flow:
        1. Get input datasets from DynamoDB
        2. Read Parquet data from S3 for each input
        3. Call Executor API with transform code and data
        4. Save output as new dataset in S3
        5. Create Dataset record in DynamoDB
        6. Update Transform.output_dataset_id

        Args:
            transform: Transform to execute
            dynamodb: DynamoDB resource instance
            s3: S3 client instance

        Returns:
            TransformExecutionResult with execution details

        Raises:
            ValueError: If input dataset not found or has no data
            RuntimeError: If executor fails after retries
        """
        start_time = time.perf_counter()

        # Step 1: Get input datasets
        dataset_repo = DatasetRepository()
        input_datasets = []
        input_dataframes = []

        for input_dataset_id in transform.input_dataset_ids:
            dataset = await dataset_repo.get_by_id(input_dataset_id, dynamodb)
            if dataset is None:
                raise ValueError(f"Input dataset '{input_dataset_id}' not found")
            if dataset.s3_path is None:
                raise ValueError(f"Input dataset '{input_dataset_id}' has no data")
            input_datasets.append(dataset)

        # Step 2: Read Parquet data from S3
        parquet_reader = ParquetReader(s3, settings.s3_bucket_datasets)
        for dataset in input_datasets:
            df = parquet_reader.read_full(dataset.s3_path)  # type: ignore
            input_dataframes.append(df)

        # Step 3: Call Executor API
        executor_result = await self._execute_with_retry(
            transform=transform,
            datasets=input_dataframes,
        )

        # Step 4 & 5: Save output and create Dataset record
        output_df = pd.DataFrame(executor_result["data"])
        output_dataset_id = str(uuid.uuid4())

        # Save to S3
        parquet_converter = ParquetConverter(s3, settings.s3_bucket_datasets)
        storage_result = parquet_converter.convert_and_save(
            df=output_df,
            dataset_id=output_dataset_id,
        )

        # Build column schema from output DataFrame
        columns = []
        for col_name in executor_result["columns"]:
            col_dtype = str(output_df[col_name].dtype)
            columns.append(
                ColumnSchema(
                    name=col_name,
                    data_type=col_dtype,
                    nullable=output_df[col_name].isnull().any(),
                )
            )

        # Create Dataset record
        now = datetime.now(timezone.utc)
        dataset_dict = {
            "id": output_dataset_id,
            "name": f"Transform Output: {transform.name}",
            "source_type": "transform",
            "row_count": executor_result["row_count"],
            "schema": [col.model_dump() for col in columns],
            "owner_id": transform.owner_id,
            "s3_path": storage_result.s3_path,
            "column_count": len(columns),
            "created_at": now,
            "updated_at": now,
        }
        await dataset_repo.create(dataset_dict, dynamodb)

        # Step 6: Update Transform.output_dataset_id
        transform_repo = TransformRepository()
        await transform_repo.update(
            transform.id,
            {"output_dataset_id": output_dataset_id},
            dynamodb,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return TransformExecutionResult(
            output_dataset_id=output_dataset_id,
            row_count=executor_result["row_count"],
            column_names=executor_result["columns"],
            execution_time_ms=elapsed_ms,
        )

    async def _execute_with_retry(
        self,
        transform: Transform,
        datasets: list[pd.DataFrame],
    ) -> dict[str, Any]:
        """Execute transform via Executor API with exponential backoff retry.

        Retries up to MAX_RETRIES times on transient errors (connection errors,
        5xx status codes). Non-retryable errors (4xx) are raised immediately.

        Args:
            transform: Transform with code to execute
            datasets: List of input DataFrames

        Returns:
            Response data dict from executor

        Raises:
            RuntimeError: If all retries are exhausted or client error occurs
        """
        last_error: Exception | None = None

        # Prepare datasets payload
        datasets_payload = [
            {
                "data": df.to_dict(orient="records"),
                "columns": df.columns.tolist(),
            }
            for df in datasets
        ]

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(
                    timeout=settings.executor_timeout_seconds
                ) as client:
                    response = await client.post(
                        f"{settings.executor_url}/execute/transform",
                        json={
                            "transform_id": transform.id,
                            "code": transform.code,
                            "datasets": datasets_payload,
                        },
                    )
                    response.raise_for_status()
                    result: dict[str, Any] = response.json()
                    return result

            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise RuntimeError(
                        f"Executor returned client error: {e.response.status_code} - {e.response.text}"
                    ) from e
                last_error = e
                logger.warning(
                    "Executor request failed (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    e,
                )

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                logger.warning(
                    "Executor request failed (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    e,
                )

            # Exponential backoff
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2**attempt)
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"Executor failed after {MAX_RETRIES} attempts: {last_error}"
        )
