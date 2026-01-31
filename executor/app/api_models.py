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
