"""SecureExecutor - 安全なPythonコード実行環境"""
import builtins
from typing import Any


class SecureExecutor:
    """安全なPythonコード実行"""

    BLOCKED_BUILTINS = frozenset({
        'open', 'exec', 'eval', 'compile',
        '__import__', 'input', 'breakpoint',
    })

    BLOCKED_MODULES = frozenset({
        'os', 'sys', 'subprocess', 'socket',
        'http', 'urllib', 'requests', 'httpx',
        'ftplib', 'smtplib', 'telnetlib',
        'pickle', 'shelve', 'marshal',
        'ctypes', 'multiprocessing', 'threading',
        'shutil', 'tempfile', 'glob', 'pathlib',
        'importlib', 'runpy', 'code', 'codeop',
        'signal', 'resource',
    })

    def __init__(self) -> None:
        self._safe_builtins = self._create_safe_builtins()

    # class定義やその他の動作に必要なダンダー
    _REQUIRED_DUNDERS = frozenset({
        '__build_class__', '__name__', '__doc__', '__spec__',
        '__loader__', '__package__',
    })

    def _create_safe_builtins(self) -> dict[str, Any]:
        """安全な組み込み関数のみを含む辞書を作成"""
        safe: dict[str, Any] = {}
        for name in dir(builtins):
            if name.startswith('_'):
                # 必要なダンダーのみ許可
                if name in self._REQUIRED_DUNDERS:
                    safe[name] = getattr(builtins, name)
                continue
            if name in self.BLOCKED_BUILTINS:
                continue
            safe[name] = getattr(builtins, name)

        # openを明示的にブロック
        safe['open'] = self._blocked_open
        # __import__をセキュアバージョンに置き換え
        safe['__import__'] = self._create_import_hook()

        return safe

    @staticmethod
    def _blocked_open(*_args: Any, **_kwargs: Any) -> None:
        raise PermissionError("ファイルアクセスは許可されていません")

    def _create_import_hook(self) -> Any:
        """禁止モジュールのインポートをブロック"""
        original_import = builtins.__import__
        blocked = self.BLOCKED_MODULES

        def secure_import(
            name: str,
            globals: dict[str, Any] | None = None,
            locals: dict[str, Any] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ) -> Any:
            top_module = name.split('.')[0]
            if top_module in blocked:
                raise ImportError(
                    f"モジュール '{name}' のインポートは許可されていません"
                )
            return original_import(name, globals, locals, fromlist, level)

        return secure_import

    def execute(
        self,
        code: str,
        inputs: dict[str, Any],
        params: dict[str, Any],
        extra_globals: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """コードを安全に実行

        Args:
            code: 実行するPythonコード
            inputs: 入力データ (DataFrameなど)
            params: パラメータ
            extra_globals: 追加のグローバル変数

        Returns:
            ローカル名前空間の内容
        """
        import pandas as pd
        import numpy as np

        globals_dict: dict[str, Any] = {
            '__builtins__': self._safe_builtins,
            '__name__': '__main__',
            'pd': pd,
            'np': np,
        }

        # plotly を安全にインポート
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            globals_dict['px'] = px
            globals_dict['go'] = go
        except Exception:
            pass

        # matplotlib/seaborn を安全にインポート
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            globals_dict['plt'] = plt
            globals_dict['sns'] = sns
        except Exception:
            pass

        # 追加のグローバル変数を注入
        if extra_globals:
            globals_dict.update(extra_globals)

        locals_dict: dict[str, Any] = {}

        compiled = compile(code, '<user_code>', 'exec')
        exec(compiled, globals_dict, locals_dict)

        return locals_dict
