"""Executor data models"""
from dataclasses import dataclass, field


@dataclass
class HTMLResult:
    """Card実行結果"""
    html: str
    used_columns: list[str] = field(default_factory=list)
    filter_applicable: list[str] = field(default_factory=list)
