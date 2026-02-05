"""DatasetSummary model for LLM prompt generation.

Spec reference: docs/data-flow.md Section 7.2
"""
import warnings
from typing import Any

from pydantic import BaseModel, ConfigDict

# Pydantic warns when a field named "schema" shadows BaseModel.schema().
# The field name is required by the data-flow spec (Section 7.2).
warnings.filterwarnings(
    "ignore",
    message='Field name "schema" in "DatasetSummary".*shadows.*',
    category=UserWarning,
)


class DatasetSummary(BaseModel):
    """Summary of a dataset used for chatbot prompt construction.

    Contains schema, statistics, and sample rows that are converted
    to a text representation suitable for LLM prompts.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str
    schema: list[dict[str, Any]]  # noqa: A003
    row_count: int
    column_count: int
    sample_rows: list[dict[str, Any]]
    statistics: dict[str, Any]

    def to_prompt_text(self) -> str:
        """Convert this summary to LLM prompt text.

        Output format (defined in docs/data-flow.md Section 7.2):

            Dataset: {name}
            行数: {row_count:,}
            列数: {column_count}

            スキーマ:
              - {col_name}: {col_type}

            統計情報:
              - {col_name}: min={min}, max={max}, mean={mean:.2f}  (numeric)
              - {col_name}: ユニーク数={unique_count}                (string)
              - {col_name}: {min} 〜 {max}                          (date/datetime)

            サンプルデータ（先頭10行）:
              1. {row_dict}
        """
        lines: list[str] = [
            f"Dataset: {self.name}",
            f"行数: {self.row_count:,}",
            f"列数: {self.column_count}",
            "",
            "スキーマ:",
        ]

        for col in self.schema:
            lines.append(f"  - {col['name']}: {col['type']}")

        lines.append("")
        lines.append("統計情報:")

        # Iterate in schema order so output is deterministic
        for col in self.schema:
            col_name = col["name"]
            if col_name not in self.statistics:
                continue
            stats = self.statistics[col_name]

            if "mean" in stats:
                lines.append(
                    f"  - {col_name}: min={stats['min']}, "
                    f"max={stats['max']}, mean={stats['mean']:.2f}"
                )
            elif "unique_count" in stats:
                lines.append(
                    f"  - {col_name}: ユニーク数={stats['unique_count']}"
                )
            elif "min" in stats:
                lines.append(
                    f"  - {col_name}: {stats['min']} 〜 {stats['max']}"
                )

        lines.append("")
        lines.append("サンプルデータ（先頭10行）:")

        for i, row in enumerate(self.sample_rows):
            lines.append(f"  {i + 1}. {row}")

        return "\n".join(lines)
