"""CSV parsing service with encoding detection and flexible import options."""

import io
from dataclasses import dataclass, field
from typing import Any, Optional

import chardet
import pandas as pd


@dataclass(frozen=True)
class CsvImportOptions:
    """Options for CSV import configuration.

    This is an immutable dataclass to ensure thread safety and prevent
    accidental modifications after creation.
    """

    encoding: Optional[str] = None
    delimiter: str = ","
    has_header: bool = True
    null_values: list[str] = field(default_factory=list)


def detect_encoding(file_bytes: bytes) -> str:
    """Detect the encoding of a CSV file.

    Uses chardet to detect encoding from the first 10KB of the file.
    Applies Japanese encoding corrections for common misdetections.

    Args:
        file_bytes: The raw bytes of the CSV file

    Returns:
        The detected encoding as a string (e.g., 'utf-8', 'cp932')
    """
    if not file_bytes:
        return "utf-8"

    # Use first 10KB for detection
    sample = file_bytes[:10 * 1024]

    # Detect encoding
    result = chardet.detect(sample)
    encoding = result.get("encoding", "utf-8")

    if not encoding:
        return "utf-8"

    # Apply Japanese encoding corrections
    encoding_lower = encoding.lower()

    # ASCII is often UTF-8 in practice
    if encoding_lower == "ascii":
        return "utf-8"

    # ISO-8859-1 and Windows-1252 might be CP932 for Japanese text
    if encoding_lower in ("iso-8859-1", "windows-1252"):
        return "cp932"

    # Normalize SHIFT_JIS variants to lowercase
    if encoding_lower == "shift_jis":
        return "shift_jis"

    # Return lowercase version for consistency
    return encoding_lower


def _build_read_params(
    encoding: str,
    options: CsvImportOptions,
    extra_params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build pandas read_csv parameters from options.

    Args:
        encoding: The encoding to use
        options: CSV import configuration
        extra_params: Additional parameters to merge

    Returns:
        Dictionary of parameters for pd.read_csv
    """
    params: dict[str, Any] = {
        "encoding": encoding,
        "delimiter": options.delimiter,
        "header": 0 if options.has_header else None,
    }

    if options.null_values:
        params["na_values"] = options.null_values

    if extra_params:
        params.update(extra_params)

    return params


def parse_preview(
    file_bytes: bytes,
    max_rows: int = 1000,
    options: Optional[CsvImportOptions] = None,
) -> pd.DataFrame:
    """Parse a preview of a CSV file with limited rows.

    Args:
        file_bytes: The raw bytes of the CSV file
        max_rows: Maximum number of rows to read (default: 1000)
        options: Optional CSV import configuration

    Returns:
        A pandas DataFrame containing the preview data
    """
    if options is None:
        options = CsvImportOptions()

    encoding = options.encoding or detect_encoding(file_bytes)
    file_like = io.BytesIO(file_bytes)
    read_params = _build_read_params(encoding, options, {"nrows": max_rows})

    try:
        df: pd.DataFrame = pd.read_csv(file_like, **read_params)
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def parse_full(
    file_bytes: bytes,
    options: Optional[CsvImportOptions] = None,
) -> pd.DataFrame:
    """Parse the entire CSV file without row limits.

    Args:
        file_bytes: The raw bytes of the CSV file
        options: Optional CSV import configuration

    Returns:
        A pandas DataFrame containing all the data
    """
    if options is None:
        options = CsvImportOptions()

    encoding = options.encoding or detect_encoding(file_bytes)
    file_like = io.BytesIO(file_bytes)
    read_params = _build_read_params(encoding, options, {"low_memory": False})

    try:
        df: pd.DataFrame = pd.read_csv(file_like, **read_params)
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
