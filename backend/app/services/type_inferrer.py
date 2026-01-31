"""Type inference service for dataset columns."""
import pandas as pd
from datetime import datetime
from typing import Any, List
from app.models.dataset import ColumnSchema


# Date and datetime format constants
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y年%m月%d日",
]

DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
]


def _is_integer(series: "pd.Series[Any]") -> bool:
    """Check if series contains only integer values."""
    try:
        pd.to_numeric(series, errors="raise")
        return all(float(x).is_integer() for x in series if pd.notna(x))
    except (ValueError, TypeError):
        return False


def _is_float(series: "pd.Series[Any]") -> bool:
    """Check if series contains numeric values."""
    try:
        pd.to_numeric(series, errors="raise")
        return True
    except (ValueError, TypeError):
        return False


def _is_bool(series: "pd.Series[Any]") -> bool:
    """Check if series contains boolean-like values."""
    bool_values = {
        "true", "false", "1", "0", "yes", "no",
        "True", "False", "TRUE", "FALSE", "YES", "NO"
    }
    unique_vals = set(str(x).strip() for x in series if pd.notna(x))
    return len(unique_vals) > 0 and unique_vals.issubset(bool_values)


def _is_date(series: "pd.Series[Any]") -> bool:
    """Check if series contains date values."""
    sample = series.dropna()
    if len(sample) == 0:
        return False

    for fmt in DATE_FORMATS:
        try:
            for val in sample:
                datetime.strptime(str(val), fmt)
            return True
        except (ValueError, TypeError):
            continue
    return False


def _is_datetime(series: "pd.Series[Any]") -> bool:
    """Check if series contains datetime values."""
    sample = series.dropna()
    if len(sample) == 0:
        return False

    for fmt in DATETIME_FORMATS:
        try:
            for val in sample:
                datetime.strptime(str(val), fmt)
            return True
        except (ValueError, TypeError):
            continue
    return False


def infer_column_type(series: "pd.Series[Any]") -> str:
    """
    Infer the data type of a pandas Series.

    Args:
        series: pandas Series to infer type from

    Returns:
        Inferred type as string: int64, float64, bool, date, datetime, or string
    """
    # Drop NULL values
    clean_series = series.dropna()

    # If empty or all NULL, return string
    if len(clean_series) == 0:
        return "string"

    # Sample to 1000 rows for large series
    if len(clean_series) > 1000:
        clean_series = clean_series.sample(n=1000, random_state=42)

    # Check types in order of specificity
    if _is_datetime(clean_series):
        return "datetime"

    if _is_date(clean_series):
        return "date"

    if _is_bool(clean_series):
        return "bool"

    if _is_integer(clean_series):
        return "int64"

    if _is_float(clean_series):
        return "float64"

    return "string"


def infer_schema(df: pd.DataFrame) -> List[ColumnSchema]:
    """
    Infer schema for all columns in a DataFrame.

    Args:
        df: pandas DataFrame to infer schema from

    Returns:
        List of ColumnSchema objects
    """
    if df.empty:
        return []

    schemas = []
    for column in df.columns:
        data_type = infer_column_type(df[column])
        nullable = df[column].isna().any()

        schemas.append(
            ColumnSchema(
                name=column,
                data_type=data_type,
                nullable=nullable
            )
        )

    return schemas


def apply_types(df: pd.DataFrame, schema: List[ColumnSchema]) -> pd.DataFrame:
    """
    Apply inferred types to DataFrame.

    Args:
        df: pandas DataFrame to apply types to
        schema: List of ColumnSchema objects with type information

    Returns:
        New DataFrame with types applied (immutable operation)
    """
    # Create a copy to ensure immutability
    result = df.copy()

    if result.empty:
        return result

    for col_schema in schema:
        col_name = col_schema.name
        data_type = col_schema.data_type

        if col_name not in result.columns:
            continue

        if data_type == "int64":
            result[col_name] = pd.to_numeric(result[col_name], errors="coerce").astype("int64")
        elif data_type == "float64":
            result[col_name] = pd.to_numeric(result[col_name], errors="coerce")
        elif data_type == "bool":
            # Convert string boolean values to actual booleans
            bool_map = {
                "true": True, "false": False,
                "True": True, "False": False,
                "TRUE": True, "FALSE": False,
                "1": True, "0": False,
                "yes": True, "no": False,
                "YES": True, "NO": False,
                "Yes": True, "No": False,
            }
            result[col_name] = result[col_name].map(bool_map).astype("bool")
        elif data_type == "date" or data_type == "datetime":
            # Try to parse with pandas to_datetime
            result[col_name] = pd.to_datetime(result[col_name], errors="coerce")
        # string type: keep as object (default)

    return result
