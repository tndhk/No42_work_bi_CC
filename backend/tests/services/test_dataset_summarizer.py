"""Tests for DatasetSummarizer service."""
import pytest
import pandas as pd
import numpy as np
from dataclasses import asdict, fields
from moto import mock_aws
import boto3

from app.core.config import settings
from app.services.parquet_storage import ParquetConverter, ParquetReader
from app.services.dataset_summarizer import DatasetSummarizer, DatasetSummary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def s3_client():
    """Create mock S3 client with a test bucket."""
    with mock_aws():
        s3 = boto3.client('s3', region_name=settings.s3_region)
        s3.create_bucket(
            Bucket=settings.s3_bucket_datasets,
            CreateBucketConfiguration={'LocationConstraint': settings.s3_region}
        )
        yield s3


@pytest.fixture
def parquet_reader(s3_client):
    """Create ParquetReader backed by the mock S3 client."""
    return ParquetReader(s3_client, settings.s3_bucket_datasets)


@pytest.fixture
def parquet_converter(s3_client):
    """Create ParquetConverter backed by the mock S3 client."""
    return ParquetConverter(s3_client, settings.s3_bucket_datasets)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with various data types."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'salary': [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
        'is_active': [True, False, True, True, False],
    })


@pytest.fixture
def sample_dataframe_with_nulls():
    """Create a sample DataFrame that contains NULL values."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', None, 'Charlie'],
        'score': [90.5, np.nan, 70.0],
    })


@pytest.fixture
def empty_dataframe():
    """Create an empty DataFrame with schema but no rows."""
    return pd.DataFrame({
        'id': pd.Series([], dtype='int64'),
        'name': pd.Series([], dtype='str'),
        'value': pd.Series([], dtype='float64'),
    })


@pytest.fixture
def large_dataframe():
    """Create a larger DataFrame for sample_rows limiting tests."""
    return pd.DataFrame({
        'id': list(range(1, 101)),
        'value': [float(x) for x in range(1, 101)],
    })


async def _save_and_get_path(converter, df, dataset_id):
    """Helper: save a DataFrame to mock S3 and return its s3_path."""
    result = await converter.convert_and_save(
        df=df, dataset_id=dataset_id, partition_column=None
    )
    return result.s3_path


# ===========================================================================
# DatasetSummary dataclass tests
# ===========================================================================

class TestDatasetSummary:
    """Test the DatasetSummary dataclass structure and behaviour."""

    def test_dataclass_has_required_fields(self):
        """DatasetSummary must expose the six specified fields."""
        field_names = {f.name for f in fields(DatasetSummary)}
        expected = {'name', 'schema', 'row_count', 'column_count',
                    'sample_rows', 'statistics'}
        assert field_names == expected

    def test_dataclass_field_types(self):
        """Each field must have the correct annotated type."""
        annotations = DatasetSummary.__annotations__
        assert annotations['name'] is str
        assert annotations['schema'] == list[dict]
        assert annotations['row_count'] is int
        assert annotations['column_count'] is int
        assert annotations['sample_rows'] == list[dict]
        assert annotations['statistics'] is dict

    def test_can_instantiate_with_all_fields(self):
        """DatasetSummary can be instantiated with explicit values."""
        summary = DatasetSummary(
            name='test',
            schema=[{'column_name': 'id', 'type': 'int64', 'nullable': False}],
            row_count=10,
            column_count=1,
            sample_rows=[{'id': 1}],
            statistics={'id': {'min': 1, 'max': 10}},
        )
        assert summary.name == 'test'
        assert summary.row_count == 10

    def test_can_convert_to_dict(self):
        """DatasetSummary can be serialised via dataclasses.asdict."""
        summary = DatasetSummary(
            name='test',
            schema=[],
            row_count=0,
            column_count=0,
            sample_rows=[],
            statistics={},
        )
        d = asdict(summary)
        assert isinstance(d, dict)
        assert d['name'] == 'test'


# ===========================================================================
# DatasetSummarizer class tests
# ===========================================================================

class TestDatasetSummarizerInit:
    """Test DatasetSummarizer constructor."""

    def test_accepts_parquet_reader(self, parquet_reader):
        """DatasetSummarizer stores the given ParquetReader."""
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        assert summarizer.parquet_reader is parquet_reader


@pytest.mark.asyncio
class TestDatasetSummarizerSummarize:
    """Test DatasetSummarizer.summarize() method."""

    async def test_returns_dataset_summary_type(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """summarize() returns a DatasetSummary instance."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-type-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='employees')

        assert isinstance(result, DatasetSummary)

    async def test_name_is_set(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """summarize() sets the name field to the provided name."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-name-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='my_dataset')

        assert result.name == 'my_dataset'

    async def test_row_count(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """summarize() reports the correct row count."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-rows-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        assert result.row_count == 5

    async def test_column_count(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """summarize() reports the correct column count."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-cols-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        assert result.column_count == 5

    # -----------------------------------------------------------------------
    # Schema tests
    # -----------------------------------------------------------------------

    async def test_schema_contains_all_columns(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """schema list has one entry per column."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-schema-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        assert len(result.schema) == 5

    async def test_schema_entry_keys(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """Each schema entry contains column_name, type, and nullable keys."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-schema-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        for entry in result.schema:
            assert 'column_name' in entry
            assert 'type' in entry
            assert 'nullable' in entry

    async def test_schema_column_names_match(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """schema column_name values match the DataFrame columns."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-schema-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        schema_names = [e['column_name'] for e in result.schema]
        assert schema_names == ['id', 'name', 'age', 'salary', 'is_active']

    async def test_schema_types_are_strings(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """schema type values are human-readable strings (not dtype objects)."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-schema-004'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        for entry in result.schema:
            assert isinstance(entry['type'], str)

    async def test_schema_nullable_with_nulls(
        self, parquet_reader, parquet_converter, sample_dataframe_with_nulls
    ):
        """nullable is True for columns that actually contain NULLs."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe_with_nulls, 'sum-nullable-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        nullable_map = {e['column_name']: e['nullable'] for e in result.schema}
        # id has no nulls
        assert nullable_map['id'] is False
        # name and score have nulls
        assert nullable_map['name'] is True
        assert nullable_map['score'] is True

    # -----------------------------------------------------------------------
    # Sample rows tests
    # -----------------------------------------------------------------------

    async def test_sample_rows_returns_list_of_dicts(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """sample_rows is a list of dicts."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-sample-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        assert isinstance(result.sample_rows, list)
        assert all(isinstance(row, dict) for row in result.sample_rows)

    async def test_sample_rows_default_limit(
        self, parquet_reader, parquet_converter, large_dataframe
    ):
        """sample_rows defaults to at most 5 rows for datasets larger than 5."""
        s3_path = await _save_and_get_path(
            parquet_converter, large_dataframe, 'sum-sample-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        assert len(result.sample_rows) == 5

    async def test_sample_rows_small_dataset_returns_all(
        self, parquet_reader, parquet_converter
    ):
        """When the dataset has fewer than 5 rows, all rows are returned."""
        small_df = pd.DataFrame({'x': [1, 2, 3]})
        s3_path = await _save_and_get_path(
            parquet_converter, small_df, 'sum-sample-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        assert len(result.sample_rows) == 3

    async def test_sample_rows_content(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """sample_rows contain the correct data from the first rows."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-sample-004'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        first_row = result.sample_rows[0]
        assert first_row['id'] == 1
        assert first_row['name'] == 'Alice'

    # -----------------------------------------------------------------------
    # Statistics tests
    # -----------------------------------------------------------------------

    async def test_statistics_is_dict(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """statistics is a dict."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-stats-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        assert isinstance(result.statistics, dict)

    async def test_statistics_numeric_columns_have_stats(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """Numeric columns include min, max, mean, median, std."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-stats-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        # 'age' is numeric
        assert 'age' in result.statistics
        age_stats = result.statistics['age']
        for key in ('min', 'max', 'mean', 'median', 'std'):
            assert key in age_stats, f"Missing '{key}' in age statistics"

    async def test_statistics_numeric_values_correct(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """Numeric statistics values are computed correctly."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-stats-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        age_stats = result.statistics['age']
        assert age_stats['min'] == 25
        assert age_stats['max'] == 45
        assert age_stats['mean'] == 35.0
        assert age_stats['median'] == 35.0

    async def test_statistics_non_numeric_columns_have_unique_count(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """Non-numeric (object/string) columns include unique_count and top_values."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'sum-stats-004'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        # 'name' is a string column
        assert 'name' in result.statistics
        name_stats = result.statistics['name']
        assert 'unique_count' in name_stats
        assert name_stats['unique_count'] == 5
        assert 'top_values' in name_stats

    async def test_statistics_null_count(
        self, parquet_reader, parquet_converter, sample_dataframe_with_nulls
    ):
        """Statistics include null_count for columns with NULLs."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe_with_nulls, 'sum-stats-005'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='test')

        assert result.statistics['name']['null_count'] == 1
        assert result.statistics['score']['null_count'] == 1
        assert result.statistics['id']['null_count'] == 0

    # -----------------------------------------------------------------------
    # Empty DataFrame edge case
    # -----------------------------------------------------------------------

    async def test_empty_dataframe(
        self, parquet_reader, parquet_converter, empty_dataframe
    ):
        """summarize() handles an empty DataFrame gracefully."""
        s3_path = await _save_and_get_path(
            parquet_converter, empty_dataframe, 'sum-empty-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.summarize(s3_path=s3_path, name='empty')

        assert result.row_count == 0
        assert result.column_count == 3
        assert result.sample_rows == []
        assert result.name == 'empty'
        # Schema should still list the columns
        assert len(result.schema) == 3


# ===========================================================================
# Fixtures for generate_summary tests
# ===========================================================================

@pytest.fixture
def mixed_type_dataframe():
    """DataFrame with numeric, string, and datetime columns."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'Alice', 'Bob'],
        'score': [85.5, 92.0, 78.3, 95.1, 88.7],
        'created_at': pd.to_datetime([
            '2024-01-01',
            '2024-02-15',
            '2024-03-20',
            '2024-04-10',
            '2024-05-05',
        ]),
    })


@pytest.fixture
def all_null_dataframe():
    """DataFrame where every column is entirely NULL."""
    return pd.DataFrame({
        'null_int': pd.array([None, None, None], dtype=pd.Int64Dtype()),
        'null_str': pd.array([None, None, None], dtype=pd.StringDtype()),
        'null_float': pd.array([None, None, None], dtype=pd.Float64Dtype()),
    })


# ===========================================================================
# generate_summary tests
# ===========================================================================

@pytest.mark.asyncio
class TestGenerateSummary:
    """Test DatasetSummarizer.generate_summary(s3_path) method.

    generate_summary uses read_preview(s3_path, 1000) to fetch a sample,
    extracts schema (name, dtype, nullable), and computes per-column statistics:
      - numeric: min, max, mean, std, null_count
      - string: unique_count, top_values (list of {value, count}), null_count
      - datetime: min, max (ISO strings), null_count
    """

    # -----------------------------------------------------------------------
    # Basic structure & contract
    # -----------------------------------------------------------------------

    async def test_returns_dict(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """generate_summary returns a plain dict."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'gs-struct-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        assert isinstance(result, dict)

    async def test_top_level_keys(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """Result contains schema, statistics, row_count, column_count."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'gs-struct-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        assert 'schema' in result
        assert 'statistics' in result
        assert 'row_count' in result
        assert 'column_count' in result

    async def test_row_and_column_counts(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """row_count and column_count match the DataFrame dimensions."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'gs-struct-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        assert result['row_count'] == 5
        assert result['column_count'] == 5

    async def test_uses_read_preview_with_1000_rows(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """generate_summary calls read_preview(s3_path, 1000)."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'gs-preview-001'
        )

        # Spy on read_preview
        original_read_preview = parquet_reader.read_preview
        call_args_log = []

        async def spy_read_preview(path, max_rows):
            call_args_log.append((path, max_rows))
            return await original_read_preview(path, max_rows)

        parquet_reader.read_preview = spy_read_preview
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)

        await summarizer.generate_summary(s3_path)

        assert len(call_args_log) == 1
        assert call_args_log[0] == (s3_path, 1000)

    # -----------------------------------------------------------------------
    # Schema
    # -----------------------------------------------------------------------

    async def test_schema_contains_all_columns(
        self, parquet_reader, parquet_converter, mixed_type_dataframe
    ):
        """Schema lists every column."""
        s3_path = await _save_and_get_path(
            parquet_converter, mixed_type_dataframe, 'gs-schema-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        col_names = [c['name'] for c in result['schema']]
        assert col_names == ['id', 'name', 'score', 'created_at']

    async def test_schema_entry_keys(
        self, parquet_reader, parquet_converter, mixed_type_dataframe
    ):
        """Each schema entry has name, dtype, and nullable."""
        s3_path = await _save_and_get_path(
            parquet_converter, mixed_type_dataframe, 'gs-schema-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        for entry in result['schema']:
            assert 'name' in entry
            assert 'dtype' in entry
            assert 'nullable' in entry

    async def test_schema_nullable_is_bool(
        self, parquet_reader, parquet_converter, mixed_type_dataframe
    ):
        """nullable is a boolean."""
        s3_path = await _save_and_get_path(
            parquet_converter, mixed_type_dataframe, 'gs-schema-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        for entry in result['schema']:
            assert isinstance(entry['nullable'], bool)

    # -----------------------------------------------------------------------
    # Numeric column statistics
    # -----------------------------------------------------------------------

    async def test_numeric_stats_keys(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """Numeric columns have min, max, mean, std, null_count."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'gs-numstat-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        age_stats = result['statistics']['age']
        for key in ('min', 'max', 'mean', 'std', 'null_count'):
            assert key in age_stats, f"Missing '{key}' in numeric statistics"

    async def test_numeric_stats_values_correct(
        self, parquet_reader, parquet_converter, sample_dataframe
    ):
        """Numeric statistics are computed correctly."""
        s3_path = await _save_and_get_path(
            parquet_converter, sample_dataframe, 'gs-numstat-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        age_stats = result['statistics']['age']
        assert age_stats['min'] == 25
        assert age_stats['max'] == 45
        assert age_stats['mean'] == pytest.approx(35.0)
        assert age_stats['null_count'] == 0

    async def test_numeric_stats_std(
        self, parquet_reader, parquet_converter
    ):
        """std is computed correctly for numeric columns."""
        df = pd.DataFrame({'val': [1, 2, 3, 4, 5]})
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-numstat-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        expected_std = pd.Series([1, 2, 3, 4, 5]).std()
        assert result['statistics']['val']['std'] == pytest.approx(expected_std)

    async def test_numeric_stats_with_nulls(
        self, parquet_reader, parquet_converter
    ):
        """null_count reflects NaN values in numeric columns."""
        df = pd.DataFrame({'val': [1.0, None, 3.0, None, 5.0]})
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-numstat-004'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        stats = result['statistics']['val']
        assert stats['null_count'] == 2
        assert stats['min'] == pytest.approx(1.0)
        assert stats['max'] == pytest.approx(5.0)
        assert stats['mean'] == pytest.approx(3.0)

    # -----------------------------------------------------------------------
    # String column statistics
    # -----------------------------------------------------------------------

    async def test_string_stats_keys(
        self, parquet_reader, parquet_converter
    ):
        """String columns have unique_count, top_values, null_count."""
        df = pd.DataFrame({'color': ['red', 'blue', 'red', 'green', 'blue']})
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-strstat-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        stats = result['statistics']['color']
        assert 'unique_count' in stats
        assert 'top_values' in stats
        assert 'null_count' in stats

    async def test_string_stats_unique_count(
        self, parquet_reader, parquet_converter
    ):
        """unique_count counts distinct non-null values."""
        df = pd.DataFrame({'color': ['red', 'blue', 'red', 'green', 'blue', 'blue']})
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-strstat-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        assert result['statistics']['color']['unique_count'] == 3

    async def test_string_stats_top_values_format(
        self, parquet_reader, parquet_converter
    ):
        """top_values is list of {value, count} dicts sorted by count desc."""
        df = pd.DataFrame({'color': ['red', 'blue', 'red', 'green', 'blue', 'blue']})
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-strstat-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        top = result['statistics']['color']['top_values']
        assert isinstance(top, list)
        # Most frequent first: blue=3
        assert top[0]['value'] == 'blue'
        assert top[0]['count'] == 3
        # Second: red=2
        assert top[1]['value'] == 'red'
        assert top[1]['count'] == 2

    async def test_string_stats_top_values_limited_to_10(
        self, parquet_reader, parquet_converter
    ):
        """top_values has at most 10 entries."""
        df = pd.DataFrame({'item': [f'item_{i}' for i in range(20)]})
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-strstat-004'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        assert len(result['statistics']['item']['top_values']) == 10

    async def test_string_stats_null_count(
        self, parquet_reader, parquet_converter
    ):
        """null_count reflects NaN values in string columns."""
        df = pd.DataFrame({'name': ['Alice', None, 'Bob', None, 'Charlie']})
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-strstat-005'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        assert result['statistics']['name']['null_count'] == 2

    # -----------------------------------------------------------------------
    # Date/datetime column statistics
    # -----------------------------------------------------------------------

    async def test_datetime_stats_min_max(
        self, parquet_reader, parquet_converter
    ):
        """Datetime columns produce min and max as ISO-format strings."""
        df = pd.DataFrame({
            'ts': pd.to_datetime(['2024-01-15', '2024-06-30', '2024-03-10']),
        })
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-datestat-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        stats = result['statistics']['ts']
        assert stats['min'] == '2024-01-15T00:00:00'
        assert stats['max'] == '2024-06-30T00:00:00'

    async def test_datetime_stats_null_count(
        self, parquet_reader, parquet_converter
    ):
        """null_count reflects NaT values in datetime columns."""
        df = pd.DataFrame({
            'ts': pd.to_datetime(['2024-01-15', None, '2024-03-10']),
        })
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-datestat-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        assert result['statistics']['ts']['null_count'] == 1

    async def test_datetime_stats_keys(
        self, parquet_reader, parquet_converter
    ):
        """Datetime column stats include min, max, null_count."""
        df = pd.DataFrame({
            'ts': pd.to_datetime(['2024-01-15', '2024-06-30']),
        })
        s3_path = await _save_and_get_path(
            parquet_converter, df, 'gs-datestat-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        stats = result['statistics']['ts']
        assert 'min' in stats
        assert 'max' in stats
        assert 'null_count' in stats

    # -----------------------------------------------------------------------
    # Edge cases
    # -----------------------------------------------------------------------

    async def test_empty_dataframe_schema_preserved(
        self, parquet_reader, parquet_converter, empty_dataframe
    ):
        """Empty DataFrame returns schema with zero rows."""
        s3_path = await _save_and_get_path(
            parquet_converter, empty_dataframe, 'gs-edge-001'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        assert result['row_count'] == 0
        col_names = [c['name'] for c in result['schema']]
        assert 'id' in col_names
        assert 'name' in col_names
        assert 'value' in col_names

    async def test_all_null_columns_no_exception(
        self, parquet_reader, parquet_converter, all_null_dataframe
    ):
        """All-null columns are handled gracefully."""
        s3_path = await _save_and_get_path(
            parquet_converter, all_null_dataframe, 'gs-edge-002'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        for col_name, col_stats in result['statistics'].items():
            assert col_stats['null_count'] == 3

    async def test_all_null_numeric_returns_none(
        self, parquet_reader, parquet_converter, all_null_dataframe
    ):
        """All-null numeric columns return None for min/max/mean/std."""
        s3_path = await _save_and_get_path(
            parquet_converter, all_null_dataframe, 'gs-edge-003'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        for col_name in ['null_int', 'null_float']:
            stats = result['statistics'][col_name]
            assert stats['min'] is None
            assert stats['max'] is None
            assert stats['mean'] is None
            assert stats['std'] is None

    async def test_mixed_type_statistics_coverage(
        self, parquet_reader, parquet_converter, mixed_type_dataframe
    ):
        """Mixed-type DataFrame produces correct stat keys per column type."""
        s3_path = await _save_and_get_path(
            parquet_converter, mixed_type_dataframe, 'gs-edge-004'
        )
        summarizer = DatasetSummarizer(parquet_reader=parquet_reader)
        result = await summarizer.generate_summary(s3_path)

        stats = result['statistics']
        # numeric: id, score
        for col in ['id', 'score']:
            for key in ('min', 'max', 'mean', 'std', 'null_count'):
                assert key in stats[col]

        # string: name
        assert 'unique_count' in stats['name']
        assert 'top_values' in stats['name']
        assert 'null_count' in stats['name']

        # datetime: created_at
        assert 'min' in stats['created_at']
        assert 'max' in stats['created_at']
        assert 'null_count' in stats['created_at']
