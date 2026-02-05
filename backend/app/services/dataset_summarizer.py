"""Dataset summarizer service for generating dataset metadata and statistics."""
from dataclasses import dataclass
from typing import Any
import logging

import pandas as pd
import numpy as np

from app.services.parquet_storage import ParquetReader

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_ROWS = 5
GENERATE_SUMMARY_PREVIEW_ROWS = 1000
TOP_VALUES_LIMIT = 10


@dataclass
class DatasetSummary:
    """Summary metadata for a dataset.

    Attributes:
        name: Human-readable dataset name.
        schema: Column definitions (column_name, type, nullable per column).
        row_count: Total number of rows.
        column_count: Total number of columns.
        sample_rows: First N rows as list of dicts.
        statistics: Per-column statistics (numeric and categorical).
    """
    name: str
    schema: list[dict]
    row_count: int
    column_count: int
    sample_rows: list[dict]
    statistics: dict


class DatasetSummarizer:
    """Generates a DatasetSummary by reading data through a ParquetReader."""

    def __init__(self, parquet_reader: ParquetReader) -> None:
        """Initialize DatasetSummarizer.

        Args:
            parquet_reader: ParquetReader instance for reading datasets from S3.
        """
        self.parquet_reader = parquet_reader

    async def summarize(
        self,
        s3_path: str,
        name: str,
        max_sample_rows: int = DEFAULT_SAMPLE_ROWS,
    ) -> DatasetSummary:
        """Read a dataset and produce its summary.

        Args:
            s3_path: S3 path to the Parquet file or directory.
            name: Human-readable name for the dataset.
            max_sample_rows: Maximum number of sample rows to include.

        Returns:
            DatasetSummary with schema, counts, sample rows and statistics.
        """
        df = await self.parquet_reader.read_full(s3_path)

        schema = self._build_schema(df)
        sample_rows = self._build_sample_rows(df, max_sample_rows)
        statistics = self._build_statistics(df)

        return DatasetSummary(
            name=name,
            schema=schema,
            row_count=len(df),
            column_count=len(df.columns),
            sample_rows=sample_rows,
            statistics=statistics,
        )

    async def generate_summary(self, s3_path: str) -> dict[str, Any]:
        """Generate a dataset summary from a Parquet file in S3.

        Processing flow:
          1. Read a sample via read_preview(s3_path, 1000)
          2. Extract schema: column name, dtype, nullable
          3. Compute per-column statistics:
             - Numeric: min, max, mean, std, null_count
             - String/object: unique_count, top_values (top 10), null_count
             - Datetime: min, max (ISO strings), null_count

        Args:
            s3_path: S3 path to the Parquet file or directory.

        Returns:
            Dict with keys: schema, statistics, row_count, column_count.
        """
        df = await self.parquet_reader.read_preview(
            s3_path, GENERATE_SUMMARY_PREVIEW_ROWS
        )

        schema = self._build_generate_schema(df)
        statistics = self._build_generate_statistics(df)

        return {
            'schema': schema,
            'statistics': statistics,
            'row_count': len(df),
            'column_count': len(df.columns),
        }

    # ------------------------------------------------------------------
    # Private helpers for generate_summary
    # ------------------------------------------------------------------

    def _build_generate_schema(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Build schema information for generate_summary.

        Args:
            df: Source DataFrame.

        Returns:
            List of dicts with name, dtype, and nullable keys.
        """
        schema: list[dict[str, Any]] = []
        for col in df.columns:
            nullable = bool(df[col].isna().any()) if len(df) > 0 else False
            schema.append({
                'name': col,
                'dtype': str(df[col].dtype),
                'nullable': nullable,
            })
        return schema

    def _build_generate_statistics(self, df: pd.DataFrame) -> dict[str, Any]:
        """Compute per-column statistics for generate_summary.

        Dispatches to type-specific helpers based on column dtype:
          - numeric -> _generate_numeric_stats
          - datetime -> _generate_datetime_stats
          - other   -> _generate_string_stats

        Args:
            df: Source DataFrame.

        Returns:
            Dict keyed by column name.
        """
        stats: dict[str, Any] = {}
        for col in df.columns:
            col_stats: dict[str, Any] = {}
            col_stats['null_count'] = int(df[col].isna().sum())

            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats.update(self._generate_numeric_stats(df[col]))
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_stats.update(self._generate_datetime_stats(df[col]))
            else:
                col_stats.update(self._generate_string_stats(df[col]))

            stats[col] = col_stats
        return stats

    def _generate_numeric_stats(self, series: pd.Series) -> dict[str, Any]:
        """Compute statistics for a numeric column.

        Args:
            series: Numeric pandas Series.

        Returns:
            Dict with min, max, mean, std.
        """
        non_null = series.dropna()
        if len(non_null) == 0:
            return {
                'min': None,
                'max': None,
                'mean': None,
                'std': None,
            }
        return {
            'min': self._to_python_scalar(series.min()),
            'max': self._to_python_scalar(series.max()),
            'mean': self._to_python_scalar(series.mean()),
            'std': self._to_python_scalar(series.std()),
        }

    def _generate_datetime_stats(self, series: pd.Series) -> dict[str, Any]:
        """Compute statistics for a datetime column.

        Args:
            series: Datetime pandas Series.

        Returns:
            Dict with min and max as ISO-format strings (or None if all NaT).
        """
        non_null = series.dropna()
        if len(non_null) == 0:
            return {
                'min': None,
                'max': None,
            }
        return {
            'min': non_null.min().isoformat(),
            'max': non_null.max().isoformat(),
        }

    def _generate_string_stats(self, series: pd.Series) -> dict[str, Any]:
        """Compute statistics for a string/object column.

        Args:
            series: String/object pandas Series.

        Returns:
            Dict with unique_count and top_values (list of {value, count}).
        """
        non_null = series.dropna()
        unique_count = int(non_null.nunique())
        value_counts = non_null.value_counts().head(TOP_VALUES_LIMIT)
        top_values = [
            {'value': str(val), 'count': int(cnt)}
            for val, cnt in value_counts.items()
        ]
        return {
            'unique_count': unique_count,
            'top_values': top_values,
        }

    # ------------------------------------------------------------------
    # Private helpers for summarize (legacy)
    # ------------------------------------------------------------------

    def _build_schema(self, df: pd.DataFrame) -> list[dict]:
        """Build column schema information.

        Args:
            df: Source DataFrame.

        Returns:
            List of dicts with column_name, type, and nullable keys.
        """
        schema: list[dict] = []
        for col in df.columns:
            nullable = bool(df[col].isna().any()) if len(df) > 0 else False
            schema.append({
                'column_name': col,
                'type': str(df[col].dtype),
                'nullable': nullable,
            })
        return schema

    def _build_sample_rows(
        self, df: pd.DataFrame, max_rows: int
    ) -> list[dict]:
        """Extract leading rows as list of dicts.

        Args:
            df: Source DataFrame.
            max_rows: Maximum rows to return.

        Returns:
            List of row dicts.
        """
        sample_df = df.head(max_rows)
        return self._dataframe_to_records(sample_df)

    def _build_statistics(self, df: pd.DataFrame) -> dict:
        """Compute per-column statistics.

        Numeric columns get min, max, mean, median, std.
        Non-numeric columns get unique_count and top_values.
        All columns get null_count.

        Args:
            df: Source DataFrame.

        Returns:
            Dict keyed by column name with statistics dicts as values.
        """
        stats: dict = {}
        for col in df.columns:
            col_stats: dict = {}
            col_stats['null_count'] = int(df[col].isna().sum())

            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats.update(self._numeric_stats(df[col]))
            else:
                col_stats.update(self._categorical_stats(df[col]))

            stats[col] = col_stats
        return stats

    def _numeric_stats(self, series: pd.Series) -> dict:
        """Compute statistics for a numeric column.

        Args:
            series: Numeric pandas Series.

        Returns:
            Dict with min, max, mean, median, std.
        """
        if len(series.dropna()) == 0:
            return {
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std': None,
            }
        return {
            'min': self._to_python_scalar(series.min()),
            'max': self._to_python_scalar(series.max()),
            'mean': self._to_python_scalar(series.mean()),
            'median': self._to_python_scalar(series.median()),
            'std': self._to_python_scalar(series.std()),
        }

    def _categorical_stats(self, series: pd.Series) -> dict:
        """Compute statistics for a non-numeric column.

        Args:
            series: Categorical/object pandas Series.

        Returns:
            Dict with unique_count and top_values (by frequency).
        """
        non_null = series.dropna()
        unique_count = int(non_null.nunique())
        top_values = (
            non_null.value_counts()
            .head(TOP_VALUES_LIMIT)
            .index
            .tolist()
        )
        return {
            'unique_count': unique_count,
            'top_values': top_values,
        }

    @staticmethod
    def _to_python_scalar(value):
        """Convert numpy/pandas scalar to native Python type.

        Args:
            value: A scalar value (possibly numpy).

        Returns:
            Native Python int, float, or the original value.
        """
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        return value

    @staticmethod
    def _dataframe_to_records(df: pd.DataFrame) -> list[dict]:
        """Convert a DataFrame to a list of plain-dict records.

        Numpy scalars are converted to Python natives for JSON safety.

        Args:
            df: DataFrame to convert.

        Returns:
            List of dicts, one per row.
        """
        records: list[dict] = []
        for row in df.to_dict(orient='records'):
            clean: dict = {}
            for k, v in row.items():
                if isinstance(v, (np.integer,)):
                    clean[k] = int(v)
                elif isinstance(v, (np.floating,)):
                    clean[k] = float(v)
                elif isinstance(v, (np.bool_,)):
                    clean[k] = bool(v)
                else:
                    clean[k] = v
            records.append(clean)
        return records
