"""Tests for DatasetSummary model and to_prompt_text() method."""
import pytest

from app.models.dataset_summary import DatasetSummary


class TestDatasetSummaryModel:
    """Test DatasetSummary model creation and validation."""

    def test_create_basic_summary(self):
        """Test creating a DatasetSummary with all required fields."""
        summary = DatasetSummary(
            name="sales_data",
            schema=[
                {"name": "date", "type": "date"},
                {"name": "amount", "type": "float64"},
            ],
            row_count=1000,
            column_count=2,
            sample_rows=[{"date": "2025-01-01", "amount": 100.0}],
            statistics={},
        )
        assert summary.name == "sales_data"
        assert summary.row_count == 1000
        assert summary.column_count == 2
        assert len(summary.schema) == 2
        assert len(summary.sample_rows) == 1

    def test_create_summary_with_empty_sample_rows(self):
        """Test creating a DatasetSummary with empty sample rows."""
        summary = DatasetSummary(
            name="empty_ds",
            schema=[{"name": "id", "type": "int64"}],
            row_count=0,
            column_count=1,
            sample_rows=[],
            statistics={},
        )
        assert summary.sample_rows == []
        assert summary.row_count == 0

    def test_create_summary_with_statistics(self):
        """Test creating a DatasetSummary with statistics dict."""
        stats = {
            "amount": {
                "null_count": 5,
                "null_ratio": 0.005,
                "min": 10.0,
                "max": 9999.0,
                "mean": 500.25,
                "std": 120.5,
            },
            "category": {
                "null_count": 0,
                "null_ratio": 0.0,
                "unique_count": 3,
                "top_values": {"A": 400, "B": 350, "C": 250},
            },
        }
        summary = DatasetSummary(
            name="test_ds",
            schema=[
                {"name": "amount", "type": "float64"},
                {"name": "category", "type": "string"},
            ],
            row_count=1000,
            column_count=2,
            sample_rows=[],
            statistics=stats,
        )
        assert summary.statistics["amount"]["mean"] == 500.25
        assert summary.statistics["category"]["unique_count"] == 3


class TestDatasetSummaryToPromptText:
    """Test DatasetSummary.to_prompt_text() output format.

    Output format is defined in docs/data-flow.md Section 7.2:
      Dataset: {name}
      行数: {row_count:,}
      列数: {column_count}

      スキーマ:
        - {col_name}: {col_type}
        ...

      統計情報:
        - {col_name}: min={min}, max={max}, mean={mean:.2f}   (for numeric)
        - {col_name}: ユニーク数={unique_count}                 (for string)
        - {col_name}: {min} 〜 {max}                            (for date/datetime)

      サンプルデータ（先頭10行）:
        1. {row_dict}
        ...
    """

    def _make_summary(self, **overrides) -> DatasetSummary:
        """Helper to create a DatasetSummary with sensible defaults."""
        defaults = dict(
            name="test_dataset",
            schema=[
                {"name": "id", "type": "int64"},
                {"name": "name", "type": "string"},
            ],
            row_count=100,
            column_count=2,
            sample_rows=[
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            statistics={},
        )
        defaults.update(overrides)
        return DatasetSummary(**defaults)

    def test_header_contains_dataset_name(self):
        """Test that output starts with 'Dataset: {name}'."""
        summary = self._make_summary(name="my_sales")
        text = summary.to_prompt_text()
        lines = text.split("\n")
        assert lines[0] == "Dataset: my_sales"

    def test_header_contains_row_count_with_comma(self):
        """Test that row count is formatted with comma separator."""
        summary = self._make_summary(row_count=1234567)
        text = summary.to_prompt_text()
        assert "行数: 1,234,567" in text

    def test_header_contains_column_count(self):
        """Test that column count is present."""
        summary = self._make_summary(column_count=5)
        text = summary.to_prompt_text()
        assert "列数: 5" in text

    def test_schema_section_present(self):
        """Test that schema section is present with correct format."""
        summary = self._make_summary(
            schema=[
                {"name": "date", "type": "date"},
                {"name": "amount", "type": "float64"},
                {"name": "category", "type": "string"},
            ]
        )
        text = summary.to_prompt_text()
        assert "スキーマ:" in text
        assert "  - date: date" in text
        assert "  - amount: float64" in text
        assert "  - category: string" in text

    def test_statistics_section_numeric_column(self):
        """Test statistics output for numeric columns with mean."""
        summary = self._make_summary(
            schema=[{"name": "amount", "type": "float64"}],
            statistics={
                "amount": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "min": 10.0,
                    "max": 500.0,
                    "mean": 255.33,
                    "std": 50.0,
                },
            },
        )
        text = summary.to_prompt_text()
        assert "統計情報:" in text
        assert "  - amount: min=10.0, max=500.0, mean=255.33" in text

    def test_statistics_section_string_column(self):
        """Test statistics output for string columns with unique count."""
        summary = self._make_summary(
            schema=[{"name": "category", "type": "string"}],
            statistics={
                "category": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "unique_count": 5,
                    "top_values": {"A": 10, "B": 8},
                },
            },
        )
        text = summary.to_prompt_text()
        assert "統計情報:" in text
        assert "  - category: ユニーク数=5" in text

    def test_statistics_section_date_column(self):
        """Test statistics output for date columns with min/max range."""
        summary = self._make_summary(
            schema=[{"name": "order_date", "type": "date"}],
            statistics={
                "order_date": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "min": "2024-01-01",
                    "max": "2025-12-31",
                },
            },
        )
        text = summary.to_prompt_text()
        assert "統計情報:" in text
        assert "  - order_date: 2024-01-01 〜 2025-12-31" in text

    def test_sample_rows_section_present(self):
        """Test that sample rows section is present with numbered rows."""
        summary = self._make_summary(
            sample_rows=[
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"},
            ]
        )
        text = summary.to_prompt_text()
        assert "サンプルデータ（先頭10行）:" in text
        assert "  1. {'id': 1, 'name': 'Alice'}" in text
        assert "  2. {'id': 2, 'name': 'Bob'}" in text
        assert "  3. {'id': 3, 'name': 'Charlie'}" in text

    def test_empty_statistics(self):
        """Test output when statistics dict is empty."""
        summary = self._make_summary(statistics={})
        text = summary.to_prompt_text()
        assert "統計情報:" in text
        # No stat lines should follow
        lines = text.split("\n")
        stats_idx = lines.index("統計情報:")
        # Next non-empty line after stats header should be the sample section
        next_content_lines = [
            l for l in lines[stats_idx + 1 :] if l.strip() != ""
        ]
        if next_content_lines:
            assert next_content_lines[0] == "サンプルデータ（先頭10行）:"

    def test_empty_sample_rows(self):
        """Test output when sample_rows is empty."""
        summary = self._make_summary(sample_rows=[])
        text = summary.to_prompt_text()
        assert "サンプルデータ（先頭10行）:" in text
        # No row lines should follow the header
        lines = text.split("\n")
        sample_idx = lines.index("サンプルデータ（先頭10行）:")
        remaining = [l for l in lines[sample_idx + 1 :] if l.strip() != ""]
        assert remaining == []

    def test_full_output_format_integration(self):
        """Integration test: verify the complete output matches expected format."""
        summary = DatasetSummary(
            name="sales_2025",
            schema=[
                {"name": "date", "type": "date"},
                {"name": "amount", "type": "float64"},
                {"name": "region", "type": "string"},
            ],
            row_count=50000,
            column_count=3,
            sample_rows=[
                {"date": "2025-01-01", "amount": 100.5, "region": "Tokyo"},
                {"date": "2025-01-02", "amount": 200.0, "region": "Osaka"},
            ],
            statistics={
                "date": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "min": "2025-01-01",
                    "max": "2025-06-30",
                },
                "amount": {
                    "null_count": 10,
                    "null_ratio": 0.0002,
                    "min": 1.0,
                    "max": 9999.99,
                    "mean": 1234.56,
                    "std": 500.0,
                },
                "region": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "unique_count": 4,
                    "top_values": {"Tokyo": 20000, "Osaka": 15000},
                },
            },
        )

        text = summary.to_prompt_text()

        expected = "\n".join([
            "Dataset: sales_2025",
            "行数: 50,000",
            "列数: 3",
            "",
            "スキーマ:",
            "  - date: date",
            "  - amount: float64",
            "  - region: string",
            "",
            "統計情報:",
            "  - date: 2025-01-01 〜 2025-06-30",
            "  - amount: min=1.0, max=9999.99, mean=1234.56",
            "  - region: ユニーク数=4",
            "",
            "サンプルデータ（先頭10行）:",
            "  1. {'date': '2025-01-01', 'amount': 100.5, 'region': 'Tokyo'}",
            "  2. {'date': '2025-01-02', 'amount': 200.0, 'region': 'Osaka'}",
        ])

        assert text == expected

    def test_mean_formatting_two_decimal_places(self):
        """Test that mean is formatted with exactly 2 decimal places."""
        summary = self._make_summary(
            schema=[{"name": "price", "type": "float64"}],
            statistics={
                "price": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "min": 1.0,
                    "max": 100.0,
                    "mean": 50.0,
                    "std": 10.0,
                },
            },
        )
        text = summary.to_prompt_text()
        # mean=50.0 should be formatted as 50.00
        assert "mean=50.00" in text

    def test_statistics_order_follows_schema_order(self):
        """Test that statistics are output in schema column order."""
        summary = DatasetSummary(
            name="ordered_ds",
            schema=[
                {"name": "alpha", "type": "float64"},
                {"name": "beta", "type": "string"},
                {"name": "gamma", "type": "date"},
            ],
            row_count=10,
            column_count=3,
            sample_rows=[],
            statistics={
                "gamma": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "min": "2024-01-01",
                    "max": "2024-12-31",
                },
                "alpha": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "min": 1.0,
                    "max": 100.0,
                    "mean": 50.0,
                    "std": 10.0,
                },
                "beta": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "unique_count": 3,
                    "top_values": {"x": 5},
                },
            },
        )
        text = summary.to_prompt_text()
        lines = text.split("\n")
        stat_lines = [l for l in lines if l.startswith("  - ")]
        # Filter to only stat lines after "統計情報:" section
        stats_section_start = lines.index("統計情報:")
        sample_section_start = lines.index("サンプルデータ（先頭10行）:")
        stat_lines = [
            l
            for l in lines[stats_section_start:sample_section_start]
            if l.startswith("  - ")
        ]
        assert len(stat_lines) == 3
        assert stat_lines[0].startswith("  - alpha:")
        assert stat_lines[1].startswith("  - beta:")
        assert stat_lines[2].startswith("  - gamma:")

    def test_row_count_zero_formatted(self):
        """Test that row_count=0 is formatted correctly."""
        summary = self._make_summary(row_count=0)
        text = summary.to_prompt_text()
        assert "行数: 0" in text

    def test_statistics_column_not_in_statistics_dict_skipped(self):
        """Test that schema columns without statistics entries are skipped."""
        summary = self._make_summary(
            schema=[
                {"name": "col_a", "type": "int64"},
                {"name": "col_b", "type": "string"},
            ],
            statistics={
                "col_a": {
                    "null_count": 0,
                    "null_ratio": 0.0,
                    "min": 1.0,
                    "max": 10.0,
                    "mean": 5.0,
                    "std": 2.0,
                },
                # col_b is intentionally absent
            },
        )
        text = summary.to_prompt_text()
        lines = text.split("\n")
        stats_section_start = lines.index("統計情報:")
        sample_section_start = lines.index("サンプルデータ（先頭10行）:")
        stat_lines = [
            l
            for l in lines[stats_section_start:sample_section_start]
            if l.startswith("  - ")
        ]
        assert len(stat_lines) == 1
        assert stat_lines[0].startswith("  - col_a:")
