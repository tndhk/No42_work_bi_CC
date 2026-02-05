"""Parquet storage service for converting and storing DataFrames in S3."""
from dataclasses import dataclass
from typing import Any
import io
import inspect
import json
import logging
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)
DEBUG_LOG_PATH = "/Users/takahikotsunoda/Dev/No42_work_bi_CC/.cursor/debug.log"


async def _maybe_await(result: Any) -> Any:
    if inspect.isawaitable(result):
        return await result
    return result


def _append_agent_log(
    session_id: str,
    run_id: str,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, Any],
) -> None:
    payload = {
        "sessionId": session_id,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        logger.debug("Failed to write agent debug log", exc_info=True)


@dataclass(frozen=True)
class StorageResult:
    """Result of storage operation.

    Attributes:
        s3_path: S3 path where data is stored
        partitioned: Whether data is partitioned
        partition_column: Column used for partitioning
        partitions: List of partition values
    """
    s3_path: str
    partitioned: bool
    partition_column: str | None
    partitions: list[str]


class ParquetConverter:
    """Converts and saves DataFrames as Parquet files to S3."""

    def __init__(self, s3_client: Any, bucket: str) -> None:
        """Initialize ParquetConverter.

        Args:
            s3_client: S3 client from boto3/aioboto3
            bucket: S3 bucket name
        """
        self.s3_client = s3_client
        self.bucket = bucket

    async def convert_and_save(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        partition_column: str | None = None
    ) -> StorageResult:
        """Convert DataFrame to Parquet and save to S3.

        Args:
            df: DataFrame to convert
            dataset_id: Dataset identifier
            partition_column: Column to partition by (optional)

        Returns:
            StorageResult with storage information
        """
        if partition_column is None:
            return await self._save_non_partitioned(df, dataset_id)
        else:
            return await self._save_partitioned(df, dataset_id, partition_column)

    async def _save_non_partitioned(
        self,
        df: pd.DataFrame,
        dataset_id: str
    ) -> StorageResult:
        """Save DataFrame without partitioning.

        Args:
            df: DataFrame to save
            dataset_id: Dataset identifier

        Returns:
            StorageResult

        Raises:
            ValueError: If DataFrame is None or dataset_id is empty
            Exception: If S3 upload fails
        """
        if df is None:
            raise ValueError("DataFrame cannot be None")
        if not dataset_id or not dataset_id.strip():
            raise ValueError("dataset_id cannot be empty")

        s3_path = f'datasets/{dataset_id}/data/part-0000.parquet'

        try:
            # Convert and upload
            parquet_bytes = self._convert_to_parquet_bytes(df)
            await self._upload_to_s3(s3_path, parquet_bytes)

            logger.info(f"Saved non-partitioned data to {s3_path}")

            return StorageResult(
                s3_path=s3_path,
                partitioned=False,
                partition_column=None,
                partitions=[]
            )
        except Exception as e:
            logger.error(f"Failed to save non-partitioned data: {e}")
            raise

    def _convert_to_parquet_bytes(self, df: pd.DataFrame) -> bytes:
        """Convert DataFrame to Parquet bytes with snappy compression.

        Args:
            df: DataFrame to convert

        Returns:
            Parquet data as bytes
        """
        table = pa.Table.from_pandas(df)
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression='snappy')
        buffer.seek(0)
        return buffer.getvalue()

    async def _upload_to_s3(self, s3_path: str, data: bytes) -> None:
        """Upload data to S3.

        Args:
            s3_path: S3 key path
            data: Data to upload
        """
        # region agent log
        _append_agent_log(
            session_id="debug-session",
            run_id="post-fix",
            hypothesis_id="A",
            location="ParquetConverter._upload_to_s3",
            message="s3 put_object start",
            data={
                "bucket": self.bucket,
                "key": s3_path,
                "sizeBytes": len(data),
            },
        )
        # endregion
        put_result = self.s3_client.put_object(
            Bucket=self.bucket,
            Key=s3_path,
            Body=data
        )
        await _maybe_await(put_result)
        # region agent log
        _append_agent_log(
            session_id="debug-session",
            run_id="post-fix",
            hypothesis_id="A",
            location="ParquetConverter._upload_to_s3",
            message="s3 put_object done",
            data={
                "bucket": self.bucket,
                "key": s3_path,
                "sizeBytes": len(data),
            },
        )
        # endregion

    async def _save_partitioned(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        partition_column: str
    ) -> StorageResult:
        """Save DataFrame with partitioning.

        Args:
            df: DataFrame to save
            dataset_id: Dataset identifier
            partition_column: Column to partition by

        Returns:
            StorageResult

        Raises:
            ValueError: If inputs are invalid or partition_column not in df
            Exception: If S3 upload fails
        """
        if df is None:
            raise ValueError("DataFrame cannot be None")
        if not dataset_id or not dataset_id.strip():
            raise ValueError("dataset_id cannot be empty")
        if partition_column not in df.columns:
            raise ValueError(f"Column '{partition_column}' not found in DataFrame")

        try:
            base_path = f'datasets/{dataset_id}/partitions/'
            partition_values = self._extract_partition_values(df, partition_column)

            # Save each partition
            await self._save_all_partitions(
                df, base_path, partition_column, partition_values
            )

            logger.info(
                f"Saved partitioned data to {base_path} "
                f"({len(partition_values)} partitions)"
            )

            # Create result with first partition path
            first_partition = partition_values[0]
            s3_path = (
                f'{base_path}{partition_column}={first_partition}/'
                f'part-0000.parquet'
            )

            return StorageResult(
                s3_path=s3_path,
                partitioned=True,
                partition_column=partition_column,
                partitions=partition_values
            )
        except Exception as e:
            logger.error(f"Failed to save partitioned data: {e}")
            raise

    def _extract_partition_values(
        self, df: pd.DataFrame, partition_column: str
    ) -> list[str]:
        """Extract unique partition values from DataFrame.

        Args:
            df: DataFrame to extract from
            partition_column: Column name

        Returns:
            List of partition values as strings
        """
        partition_values = df[partition_column].unique().tolist()
        return [str(v) for v in partition_values]

    async def _save_all_partitions(
        self,
        df: pd.DataFrame,
        base_path: str,
        partition_column: str,
        partition_values: list[str]
    ) -> None:
        """Save all partitions to S3.

        Args:
            df: DataFrame to partition
            base_path: Base S3 path
            partition_column: Column to partition by
            partition_values: List of partition values
        """
        for partition_value in partition_values:
            await self._save_single_partition(
                df, base_path, partition_column, partition_value
            )

    async def _save_single_partition(
        self,
        df: pd.DataFrame,
        base_path: str,
        partition_column: str,
        partition_value: str
    ) -> None:
        """Save a single partition to S3.

        Args:
            df: Full DataFrame
            base_path: Base S3 path
            partition_column: Column to partition by
            partition_value: Value for this partition
        """
        partition_df = df[df[partition_column] == partition_value]
        s3_path = (
            f'{base_path}{partition_column}={partition_value}/'
            f'part-0000.parquet'
        )

        parquet_bytes = self._convert_to_parquet_bytes(partition_df)
        await self._upload_to_s3(s3_path, parquet_bytes)


class ParquetReader:
    """Reads Parquet files from S3."""

    def __init__(self, s3_client: Any, bucket: str) -> None:
        """Initialize ParquetReader.

        Args:
            s3_client: S3 client from boto3/aioboto3
            bucket: S3 bucket name
        """
        self.s3_client = s3_client
        self.bucket = bucket

    async def read_full(self, s3_path: str) -> pd.DataFrame:
        """Read full Parquet dataset from S3.

        Args:
            s3_path: S3 path (can be file or directory)

        Returns:
            DataFrame with all data
        """
        # Check if path is a directory (ends with /)
        if s3_path.endswith('/'):
            return await self._read_partitioned(s3_path)
        else:
            return await self._read_single_file(s3_path)

    async def read_preview(self, s3_path: str, max_rows: int) -> pd.DataFrame:
        """Read preview of Parquet dataset from S3.

        Args:
            s3_path: S3 path (can be file or directory)
            max_rows: Maximum number of rows to return

        Returns:
            DataFrame with limited rows
        """
        df = await self.read_full(s3_path)
        return df.head(max_rows)

    async def _read_single_file(self, s3_path: str) -> pd.DataFrame:
        """Read single Parquet file from S3.

        Args:
            s3_path: S3 file path

        Returns:
            DataFrame

        Raises:
            Exception: If S3 read or Parquet parsing fails
        """
        try:
            # region agent log
            _append_agent_log(
                session_id="debug-session",
                run_id="post-fix",
                hypothesis_id="B",
                location="ParquetReader._read_single_file",
                message="s3 get_object start",
                data={
                    "bucket": self.bucket,
                    "key": s3_path,
                },
            )
            # endregion
            response = await _maybe_await(self.s3_client.get_object(
                Bucket=self.bucket,
                Key=s3_path
            ))
            read_result = response['Body'].read()
            parquet_data = await _maybe_await(read_result)
            # region agent log
            _append_agent_log(
                session_id="debug-session",
                run_id="post-fix",
                hypothesis_id="B",
                location="ParquetReader._read_single_file",
                message="s3 get_object done",
                data={
                    "bucket": self.bucket,
                    "key": s3_path,
                    "sizeBytes": len(parquet_data),
                },
            )
            # endregion

            parquet_file = pq.ParquetFile(io.BytesIO(parquet_data))
            table = parquet_file.read()

            result: pd.DataFrame = table.to_pandas()
            return result
        except Exception as e:
            # region agent log
            _append_agent_log(
                session_id="debug-session",
                run_id="post-fix",
                hypothesis_id="C",
                location="ParquetReader._read_single_file",
                message="s3 get_object error",
                data={
                    "bucket": self.bucket,
                    "key": s3_path,
                    "error": str(e),
                },
            )
            # endregion
            logger.error(f"Failed to read file from {s3_path}: {e}")
            raise

    async def _read_partitioned(self, base_path: str) -> pd.DataFrame:
        """Read partitioned Parquet dataset from S3.

        Args:
            base_path: Base path for partitioned data

        Returns:
            DataFrame with all partitions combined

        Raises:
            Exception: If S3 list or read operations fail
        """
        try:
            response = await _maybe_await(self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=base_path
            ))

            if 'Contents' not in response:
                logger.warning(f"No files found at {base_path}")
                return pd.DataFrame()

            parquet_files = self._filter_parquet_files(response['Contents'])

            if not parquet_files:
                logger.warning(f"No parquet files found at {base_path}")
                return pd.DataFrame()

            dfs = [await self._read_single_file(key) for key in parquet_files]

            return pd.concat(dfs, ignore_index=True)
        except Exception as e:
            logger.error(f"Failed to read partitioned data from {base_path}: {e}")
            raise

    def _filter_parquet_files(self, contents: list[dict[str, Any]]) -> list[str]:
        """Filter parquet files from S3 object list.

        Args:
            contents: S3 object list

        Returns:
            List of parquet file keys
        """
        return [
            obj['Key'] for obj in contents
            if obj['Key'].endswith('.parquet')
        ]
