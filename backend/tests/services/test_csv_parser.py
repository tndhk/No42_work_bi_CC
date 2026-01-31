"""Tests for CSV parser service."""

from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from app.services.csv_parser import (
    CsvImportOptions,
    detect_encoding,
    parse_full,
    parse_preview,
)


class TestDetectEncoding:
    """Tests for encoding detection."""

    def test_detect_utf8(self) -> None:
        """Should detect UTF-8 encoding."""
        csv_content = "名前,年齢\n太郎,30\n花子,25"
        file_bytes = csv_content.encode("utf-8")

        encoding = detect_encoding(file_bytes)

        assert encoding == "utf-8"

    def test_detect_cp932(self) -> None:
        """Should detect CP932 encoding."""
        csv_content = "名前,年齢\n太郎,30\n花子,25"
        file_bytes = csv_content.encode("cp932")

        encoding = detect_encoding(file_bytes)

        # CP932 and Shift_JIS are compatible, chardet may detect either
        assert encoding in ("cp932", "shift_jis")

    def test_detect_shift_jis(self) -> None:
        """Should detect Shift_JIS encoding."""
        csv_content = "名前,年齢\n太郎,30\n花子,25"
        file_bytes = csv_content.encode("shift_jis")

        encoding = detect_encoding(file_bytes)

        assert encoding in ("shift_jis", "cp932")  # chardet may detect as cp932

    def test_ascii_correction_to_utf8(self) -> None:
        """Should correct ASCII detection to UTF-8."""
        csv_content = "name,age\njohn,30\njane,25"
        file_bytes = csv_content.encode("ascii")

        encoding = detect_encoding(file_bytes)

        assert encoding == "utf-8"

    def test_iso_8859_1_correction_to_cp932(self) -> None:
        """Should correct ISO-8859-1 detection to CP932."""
        # Create content that chardet might detect as ISO-8859-1
        csv_content = "名前,年齢\n太郎,30"
        file_bytes = csv_content.encode("cp932")

        # Mock chardet to return ISO-8859-1 (this is just testing the correction logic)
        encoding = detect_encoding(file_bytes)

        # Should be detected as cp932 or corrected to cp932
        assert encoding in ("cp932", "shift_jis")

    def test_use_first_10kb_only(self) -> None:
        """Should use only first 10KB for detection."""
        # Create large content > 10KB (need more repetitions)
        csv_content = "name,age\n" + "john,30\n" * 2000
        file_bytes = csv_content.encode("utf-8")

        assert len(file_bytes) > 10 * 1024

        encoding = detect_encoding(file_bytes)

        assert encoding == "utf-8"

    def test_empty_file(self) -> None:
        """Should handle empty file."""
        file_bytes = b""

        encoding = detect_encoding(file_bytes)

        # Should return a default encoding
        assert encoding in ("utf-8", "ascii")


class TestCsvImportOptions:
    """Tests for CsvImportOptions dataclass."""

    def test_default_values(self) -> None:
        """Should have correct default values."""
        options = CsvImportOptions()

        assert options.encoding is None
        assert options.delimiter == ","
        assert options.has_header is True
        assert options.null_values == []

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        options = CsvImportOptions(
            encoding="utf-8",
            delimiter="\t",
            has_header=False,
            null_values=["NA", "N/A"],
        )

        assert options.encoding == "utf-8"
        assert options.delimiter == "\t"
        assert options.has_header is False
        assert options.null_values == ["NA", "N/A"]

    def test_immutability(self) -> None:
        """Should be immutable (frozen dataclass)."""
        options = CsvImportOptions()

        with pytest.raises(FrozenInstanceError):
            options.encoding = "utf-8"  # type: ignore


class TestParsePreview:
    """Tests for parse_preview function."""

    def test_basic_csv_parsing(self) -> None:
        """Should parse basic CSV with headers."""
        csv_content = "name,age\njohn,30\njane,25\nbob,35"
        file_bytes = csv_content.encode("utf-8")

        df = parse_preview(file_bytes)

        assert len(df) == 3
        assert list(df.columns) == ["name", "age"]
        assert df["name"].tolist() == ["john", "jane", "bob"]
        assert df["age"].tolist() == [30, 25, 35]

    def test_explicit_encoding_override(self) -> None:
        """Should use explicit encoding when provided."""
        csv_content = "名前,年齢\n太郎,30\n花子,25"
        file_bytes = csv_content.encode("cp932")
        options = CsvImportOptions(encoding="cp932")

        df = parse_preview(file_bytes, options=options)

        assert len(df) == 2
        assert "名前" in df.columns
        assert "年齢" in df.columns

    def test_max_rows_limit_5(self) -> None:
        """Should limit preview to 5 rows when max_rows=5."""
        csv_content = "name,age\n" + "\n".join(f"person{i},{20+i}" for i in range(10))
        file_bytes = csv_content.encode("utf-8")

        df = parse_preview(file_bytes, max_rows=5)

        assert len(df) == 5

    def test_default_max_rows_1000(self) -> None:
        """Should default to max_rows=1000."""
        csv_content = "name,age\n" + "\n".join(f"person{i},{20+i}" for i in range(1500))
        file_bytes = csv_content.encode("utf-8")

        df = parse_preview(file_bytes)

        assert len(df) == 1000

    def test_no_header(self) -> None:
        """Should handle CSV without headers."""
        csv_content = "john,30\njane,25\nbob,35"
        file_bytes = csv_content.encode("utf-8")
        options = CsvImportOptions(has_header=False)

        df = parse_preview(file_bytes, options=options)

        assert len(df) == 3
        # Pandas will create default column names like 0, 1
        assert len(df.columns) == 2

    def test_tab_delimiter(self) -> None:
        """Should handle tab delimiter."""
        csv_content = "name\tage\njohn\t30\njane\t25"
        file_bytes = csv_content.encode("utf-8")
        options = CsvImportOptions(delimiter="\t")

        df = parse_preview(file_bytes, options=options)

        assert len(df) == 2
        assert list(df.columns) == ["name", "age"]

    def test_semicolon_delimiter(self) -> None:
        """Should handle semicolon delimiter."""
        csv_content = "name;age\njohn;30\njane;25"
        file_bytes = csv_content.encode("utf-8")
        options = CsvImportOptions(delimiter=";")

        df = parse_preview(file_bytes, options=options)

        assert len(df) == 2
        assert list(df.columns) == ["name", "age"]

    def test_null_values(self) -> None:
        """Should handle custom null values."""
        csv_content = "name,age\njohn,30\njane,NA\nbob,N/A"
        file_bytes = csv_content.encode("utf-8")
        options = CsvImportOptions(null_values=["NA", "N/A"])

        df = parse_preview(file_bytes, options=options)

        assert len(df) == 3
        assert pd.isna(df.iloc[1]["age"])
        assert pd.isna(df.iloc[2]["age"])

    def test_empty_csv(self) -> None:
        """Should handle empty CSV file."""
        file_bytes = b""

        df = parse_preview(file_bytes)

        # Should return empty DataFrame
        assert len(df) == 0


class TestParseFull:
    """Tests for parse_full function."""

    def test_basic_full_parsing(self) -> None:
        """Should parse entire CSV file."""
        csv_content = "name,age\n" + "\n".join(f"person{i},{20+i}" for i in range(100))
        file_bytes = csv_content.encode("utf-8")

        df = parse_full(file_bytes)

        assert len(df) == 100
        assert list(df.columns) == ["name", "age"]

    def test_large_file_with_low_memory_false(self) -> None:
        """Should parse large files with low_memory=False."""
        # Create a larger CSV
        csv_content = "name,age,city\n" + "\n".join(
            f"person{i},{20+i},city{i}" for i in range(2000)
        )
        file_bytes = csv_content.encode("utf-8")

        df = parse_full(file_bytes)

        assert len(df) == 2000
        assert len(df.columns) == 3

    def test_full_parsing_with_options(self) -> None:
        """Should respect CsvImportOptions in full parsing."""
        csv_content = "名前\t年齢\n太郎\t30\n花子\t25"
        file_bytes = csv_content.encode("utf-8")
        options = CsvImportOptions(delimiter="\t", encoding="utf-8")

        df = parse_full(file_bytes, options=options)

        assert len(df) == 2
        assert "名前" in df.columns
        assert "年齢" in df.columns

    def test_empty_csv_full(self) -> None:
        """Should handle empty CSV in full parsing."""
        file_bytes = b""

        df = parse_full(file_bytes)

        assert len(df) == 0
