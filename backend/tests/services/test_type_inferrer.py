"""Tests for type_inferrer service."""
import pandas as pd
import pytest
from datetime import datetime, date
from app.services.type_inferrer import (
    infer_column_type,
    infer_schema,
    apply_types,
)
from app.models.dataset import ColumnSchema


class TestInferColumnType:
    """Tests for infer_column_type function."""

    def test_integer_type_inference(self):
        """Test integer type is correctly inferred."""
        series = pd.Series([1, 2, 3, 4, 5])
        result = infer_column_type(series)
        assert result == "int64"

    def test_float_type_inference(self):
        """Test float type is correctly inferred."""
        series = pd.Series([1.1, 2.2, 3.3, 4.4, 5.5])
        result = infer_column_type(series)
        assert result == "float64"

    def test_mixed_numeric_with_decimal_is_float(self):
        """Test mixed integers and floats are inferred as float."""
        series = pd.Series([1, 2.5, 3, 4.1, 5])
        result = infer_column_type(series)
        assert result == "float64"

    def test_boolean_type_inference_true_false(self):
        """Test boolean type is correctly inferred from true/false."""
        series = pd.Series(["true", "false", "true", "false"])
        result = infer_column_type(series)
        assert result == "bool"

    def test_boolean_type_inference_1_0(self):
        """Test boolean type is correctly inferred from 1/0."""
        series = pd.Series(["1", "0", "1", "0"])
        result = infer_column_type(series)
        assert result == "bool"

    def test_boolean_type_inference_yes_no(self):
        """Test boolean type is correctly inferred from yes/no."""
        series = pd.Series(["yes", "no", "yes", "no"])
        result = infer_column_type(series)
        assert result == "bool"

    def test_date_type_inference_yyyy_mm_dd_hyphen(self):
        """Test date type is correctly inferred with YYYY-MM-DD format."""
        series = pd.Series(["2024-01-15", "2024-02-20", "2024-03-25"])
        result = infer_column_type(series)
        assert result == "date"

    def test_date_type_inference_yyyy_mm_dd_slash(self):
        """Test date type is correctly inferred with YYYY/MM/DD format."""
        series = pd.Series(["2024/01/15", "2024/02/20", "2024/03/25"])
        result = infer_column_type(series)
        assert result == "date"

    def test_date_type_inference_japanese(self):
        """Test date type is correctly inferred with Japanese format."""
        series = pd.Series(["2024年01月15日", "2024年02月20日", "2024年03月25日"])
        result = infer_column_type(series)
        assert result == "date"

    def test_datetime_type_inference_iso8601(self):
        """Test datetime type is correctly inferred with ISO 8601 format."""
        series = pd.Series([
            "2024-01-15T10:30:00",
            "2024-02-20T14:45:00",
            "2024-03-25T08:15:00"
        ])
        result = infer_column_type(series)
        assert result == "datetime"

    def test_datetime_type_inference_with_space(self):
        """Test datetime type is correctly inferred with space separator."""
        series = pd.Series([
            "2024-01-15 10:30:00",
            "2024-02-20 14:45:00",
            "2024-03-25 08:15:00"
        ])
        result = infer_column_type(series)
        assert result == "datetime"

    def test_string_type_inference(self):
        """Test string type is correctly inferred."""
        series = pd.Series(["apple", "banana", "cherry"])
        result = infer_column_type(series)
        assert result == "string"

    def test_all_null_returns_string(self):
        """Test all NULL values return string type."""
        series = pd.Series([None, None, None, None])
        result = infer_column_type(series)
        assert result == "string"

    def test_empty_series_returns_string(self):
        """Test empty series returns string type."""
        series = pd.Series([], dtype=object)
        result = infer_column_type(series)
        assert result == "string"

    def test_null_values_are_dropped_before_inference(self):
        """Test NULL values are dropped before type inference."""
        series = pd.Series([1, 2, None, 3, None, 4])
        result = infer_column_type(series)
        assert result == "int64"

    def test_mixed_types_return_string(self):
        """Test mixed incompatible types return string."""
        series = pd.Series([1, "text", 3.5, "2024-01-01"])
        result = infer_column_type(series)
        assert result == "string"

    def test_large_series_samples_1000_rows(self):
        """Test large series is sampled to 1000 rows."""
        # Create series with 2000 integers
        series = pd.Series(range(2000))
        result = infer_column_type(series)
        assert result == "int64"


class TestInferSchema:
    """Tests for infer_schema function."""

    def test_infer_schema_multiple_columns(self):
        """Test schema inference for multiple columns."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "score": [95.5, 87.2, 92.8],
            "passed": ["true", "false", "true"],
            "birth_date": ["1990-01-15", "1985-05-20", "1992-11-30"]
        })
        result = infer_schema(df)

        assert len(result) == 5
        assert isinstance(result[0], ColumnSchema)

        # Check types
        types = {col.name: col.data_type for col in result}
        assert types["id"] == "int64"
        assert types["name"] == "string"
        assert types["score"] == "float64"
        assert types["passed"] == "bool"
        assert types["birth_date"] == "date"

    def test_infer_schema_empty_dataframe(self):
        """Test schema inference for empty DataFrame."""
        df = pd.DataFrame()
        result = infer_schema(df)
        assert result == []

    def test_infer_schema_preserves_column_order(self):
        """Test schema inference preserves column order."""
        df = pd.DataFrame({
            "z_col": [1, 2, 3],
            "a_col": ["x", "y", "z"],
            "m_col": [1.1, 2.2, 3.3]
        })
        result = infer_schema(df)

        column_names = [col.name for col in result]
        assert column_names == ["z_col", "a_col", "m_col"]

    def test_infer_schema_with_nullable_columns(self):
        """Test schema inference correctly identifies nullable columns."""
        df = pd.DataFrame({
            "required": [1, 2, 3],
            "optional": [1, None, 3]
        })
        result = infer_schema(df)

        nullable = {col.name: col.nullable for col in result}
        assert nullable["required"] is False
        assert nullable["optional"] is True


class TestApplyTypes:
    """Tests for apply_types function."""

    def test_apply_types_converts_integer(self):
        """Test apply_types correctly converts to integer."""
        df = pd.DataFrame({"num": ["1", "2", "3"]})
        schema = [ColumnSchema(name="num", data_type="int64", nullable=False)]

        result = apply_types(df, schema)

        assert result["num"].dtype == "int64"
        assert result["num"].tolist() == [1, 2, 3]

    def test_apply_types_converts_float(self):
        """Test apply_types correctly converts to float."""
        df = pd.DataFrame({"value": ["1.1", "2.2", "3.3"]})
        schema = [ColumnSchema(name="value", data_type="float64", nullable=False)]

        result = apply_types(df, schema)

        assert result["value"].dtype == "float64"
        assert result["value"].tolist() == [1.1, 2.2, 3.3]

    def test_apply_types_converts_boolean(self):
        """Test apply_types correctly converts to boolean."""
        df = pd.DataFrame({"flag": ["true", "false", "true"]})
        schema = [ColumnSchema(name="flag", data_type="bool", nullable=False)]

        result = apply_types(df, schema)

        assert result["flag"].dtype == "bool"
        assert result["flag"].tolist() == [True, False, True]

    def test_apply_types_converts_date(self):
        """Test apply_types correctly converts to date."""
        df = pd.DataFrame({"date_col": ["2024-01-15", "2024-02-20", "2024-03-25"]})
        schema = [ColumnSchema(name="date_col", data_type="date", nullable=False)]

        result = apply_types(df, schema)

        assert pd.api.types.is_datetime64_any_dtype(result["date_col"])

    def test_apply_types_converts_datetime(self):
        """Test apply_types correctly converts to datetime."""
        df = pd.DataFrame({
            "timestamp": ["2024-01-15 10:30:00", "2024-02-20 14:45:00"]
        })
        schema = [ColumnSchema(name="timestamp", data_type="datetime", nullable=False)]

        result = apply_types(df, schema)

        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])

    def test_apply_types_keeps_string_unchanged(self):
        """Test apply_types keeps string type unchanged."""
        df = pd.DataFrame({"text": ["apple", "banana", "cherry"]})
        schema = [ColumnSchema(name="text", data_type="string", nullable=False)]

        result = apply_types(df, schema)

        assert result["text"].dtype == "object"
        assert result["text"].tolist() == ["apple", "banana", "cherry"]

    def test_apply_types_multiple_columns(self):
        """Test apply_types correctly converts multiple columns."""
        df = pd.DataFrame({
            "id": ["1", "2", "3"],
            "name": ["Alice", "Bob", "Charlie"],
            "score": ["95.5", "87.2", "92.8"]
        })
        schema = [
            ColumnSchema(name="id", data_type="int64", nullable=False),
            ColumnSchema(name="name", data_type="string", nullable=False),
            ColumnSchema(name="score", data_type="float64", nullable=False)
        ]

        result = apply_types(df, schema)

        assert result["id"].dtype == "int64"
        assert result["name"].dtype == "object"
        assert result["score"].dtype == "float64"

    def test_apply_types_is_immutable(self):
        """Test apply_types does not mutate original DataFrame."""
        df = pd.DataFrame({"num": ["1", "2", "3"]})
        original_dtype = df["num"].dtype
        schema = [ColumnSchema(name="num", data_type="int64", nullable=False)]

        result = apply_types(df, schema)

        # Original DataFrame should remain unchanged
        assert df["num"].dtype == original_dtype
        assert df["num"].tolist() == ["1", "2", "3"]

        # Result should be a new DataFrame with converted types
        assert result["num"].dtype == "int64"
        assert result["num"].tolist() == [1, 2, 3]

        # Verify they are different objects
        assert id(df) != id(result)

    def test_apply_types_empty_dataframe(self):
        """Test apply_types handles empty DataFrame."""
        df = pd.DataFrame()
        schema = []

        result = apply_types(df, schema)

        assert result.empty
        assert id(df) != id(result)
