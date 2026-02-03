"""TransformRunner - Transform実行エンジン"""
import time
from dataclasses import dataclass

from typing import Any

import pandas as pd

from app.sandbox import SecureExecutor
from app.resource_limiter import ResourceLimiter


@dataclass
class TransformResult:
    """Transform実行結果"""
    df: pd.DataFrame
    execution_time_ms: float


class TransformRunner:
    """Transform実行エンジン"""

    def __init__(
        self,
        timeout_seconds: int = 300,
        max_memory_mb: int = 4096,
    ) -> None:
        self._executor = SecureExecutor()
        self._limiter = ResourceLimiter(
            timeout_seconds=timeout_seconds,
            max_memory_mb=max_memory_mb,
        )

    def execute(
        self,
        code: str,
        inputs: dict[str, pd.DataFrame],
        params: dict[str, Any],
    ) -> TransformResult:
        """Transformコードを実行してDataFrameを生成

        Args:
            code: transform関数を含むPythonコード
            inputs: {dataset_id: DataFrame, ...} の辞書
            params: ユーザー定義パラメータ

        Returns:
            TransformResult

        Raises:
            ValueError: transform関数が未定義、または不正な戻り値
            TimeoutError: 実行タイムアウト
        """
        start_time = time.perf_counter()

        with self._limiter.limit():
            # コードをSecureExecutor内で実行
            local_ns = self._executor.execute(code, {}, {})

            # transform関数を取得
            if 'transform' not in local_ns:
                raise ValueError("コードにtransform関数が定義されていません")

            transform_func = local_ns['transform']

            # transform関数を実行
            result = transform_func(inputs, params)

        # 結果をDataFrameとして検証
        if not isinstance(result, pd.DataFrame):
            raise ValueError("transform関数はDataFrameを返す必要があります")

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return TransformResult(df=result, execution_time_ms=elapsed_ms)
