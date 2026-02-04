"""Transform execution history models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TransformExecution(BaseModel):
    """Transform execution history record."""

    model_config = ConfigDict(from_attributes=True)

    execution_id: str
    transform_id: str
    status: str              # "running" | "success" | "failed"
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    output_row_count: Optional[int] = None
    output_dataset_id: Optional[str] = None
    error: Optional[str] = None
    triggered_by: str        # "manual" | "schedule"
