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

        2つのスタイルをサポート:
        - function-based: def transform(inputs, params) を定義し DataFrame を返す
        - inline: df_0, inputs, params をグローバルで参照し result に代入する

        Args:
            code: transform関数またはinlineコードを含むPythonコード
            inputs: {dataset_id: DataFrame, ...} の辞書
            params: ユーザー定義パラメータ

        Returns:
            TransformResult

        Raises:
            ValueError: transform関数/result変数が未定義、または不正な戻り値
            TimeoutError: 実行タイムアウト
        """
        start_time = time.perf_counter()

        # inline スタイル用の extra_globals を構築
        input_dfs = list(inputs.values())
        extra_globals: dict[str, Any] = {
            f"df_{i}": df for i, df in enumerate(input_dfs)
        }
        extra_globals["inputs"] = inputs
        extra_globals["params"] = params

        with self._limiter.limit():
            # コードをSecureExecutor内で実行
            local_ns = self._executor.execute(
                code, inputs, params, extra_globals=extra_globals,
            )

            if 'transform' in local_ns:
                # function-based スタイル: transform関数を実行
                transform_func = local_ns['transform']
                result = transform_func(inputs, params)
            elif 'result' in local_ns:
                # inline スタイル: result 変数を取得
                result = local_ns['result']
            else:
                raise ValueError(
                    "コードには 'transform' 関数または 'result' 変数が必要です"
                )

        # 結果をDataFrameとして検証
        if not isinstance(result, pd.DataFrame):
            raise ValueError("transform関数はDataFrameを返す必要があります")

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return TransformResult(df=result, execution_time_ms=elapsed_ms)
