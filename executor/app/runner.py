"""CardRunner - カード実行エンジン"""
import pandas as pd
from typing import Any

from app.models import HTMLResult
from app.sandbox import SecureExecutor
from app.resource_limiter import ResourceLimiter


class CardRunner:
    """カード実行エンジン"""

    def __init__(
        self,
        timeout_seconds: int = 10,
        max_memory_mb: int = 2048,
    ) -> None:
        self._executor = SecureExecutor()
        self._limiter = ResourceLimiter(
            timeout_seconds=timeout_seconds,
            max_memory_mb=max_memory_mb,
        )

    def execute(
        self,
        code: str,
        dataset_df: pd.DataFrame,
        filters: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> HTMLResult:
        """カードコードを実行してHTMLを生成

        Args:
            code: render関数を含むPythonコード
            dataset_df: 入力DataFrame
            filters: フィルタパラメータ
            params: カード固有パラメータ

        Returns:
            HTMLResult

        Raises:
            ValueError: render関数が未定義、または不正な戻り値
            TimeoutError: 実行タイムアウト
        """
        filters = filters or {}
        params = params or {}

        with self._limiter.limit():
            # コードをSecureExecutor内で実行
            # HTMLResultはglobalsに直接注入する
            local_ns = self._executor.execute(
                code, {}, {},
                extra_globals={'HTMLResult': HTMLResult},
            )

            # render関数を取得
            if 'render' not in local_ns:
                raise ValueError("コードにrender関数が定義されていません")

            render_func = local_ns['render']

            # render関数を実行
            result = render_func(dataset_df, filters, params)

        # 結果をHTMLResultに変換
        if isinstance(result, str):
            return HTMLResult(html=result)
        if hasattr(result, 'html'):
            return HTMLResult(
                html=result.html,
                used_columns=getattr(result, 'used_columns', []) or [],
                filter_applicable=getattr(result, 'filter_applicable', []) or [],
            )

        raise ValueError("render関数はstr または HTMLResultを返す必要があります")
