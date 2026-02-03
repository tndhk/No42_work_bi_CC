"""Executor API request/response models"""
from pydantic import BaseModel
from typing import Any, Optional


class ExecuteCardRequest(BaseModel):
    """POST /execute/card リクエストボディ"""
    card_id: str
    code: str
    dataset_id: str
    filters: dict[str, Any] = {}
    params: dict[str, Any] = {}
    # dataset_rows は将来的にBackendから送信
    dataset_rows: Optional[list[dict[str, Any]]] = None


class ExecuteCardResponse(BaseModel):
    """POST /execute/card レスポンスボディ"""
    html: str
    used_columns: list[str] = []
    filter_applicable: list[str] = []
    execution_time_ms: int


class ExecuteErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: str
    detail: Optional[str] = None


class ExecuteTransformRequest(BaseModel):
    """POST /execute/transform リクエストボディ"""
    transform_id: str
    code: str
    input_datasets: dict[str, list[dict[str, Any]]]  # {dataset_id: rows}
    params: dict[str, Any] = {}


class ExecuteTransformResponse(BaseModel):
    """POST /execute/transform レスポンスボディ"""
    output_rows: list[dict[str, Any]]
    row_count: int
    column_names: list[str]
    execution_time_ms: float
