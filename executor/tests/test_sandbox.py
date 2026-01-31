"""SecureExecutor テスト"""
import pytest


class TestSecureExecutor:
    """SecureExecutor のテスト"""

    def _make_executor(self):
        from app.sandbox import SecureExecutor
        return SecureExecutor()

    def test_execute_simple_code(self):
        """基本的なPythonコードが実行できる"""
        executor = self._make_executor()
        result = executor.execute("x = 1 + 2", {}, {})
        assert result["x"] == 3

    def test_execute_with_pandas(self):
        """pandasが使用可能"""
        executor = self._make_executor()
        code = "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2, 3]})\nresult = len(df)"
        result = executor.execute(code, {}, {})
        assert result["result"] == 3

    def test_execute_with_numpy(self):
        """numpyが使用可能"""
        executor = self._make_executor()
        code = "import numpy as np\narr = np.array([1, 2, 3])\nresult = arr.sum()"
        result = executor.execute(code, {}, {})
        assert result["result"] == 6

    def test_blocks_open(self):
        """open() が禁止される"""
        executor = self._make_executor()
        with pytest.raises(PermissionError, match="ファイルアクセスは許可されていません"):
            executor.execute("f = open('/etc/passwd')", {}, {})

    def test_blocks_exec(self):
        """exec が組み込み関数から除去される"""
        executor = self._make_executor()
        with pytest.raises(NameError):
            executor.execute("exec('x = 1')", {}, {})

    def test_blocks_eval(self):
        """eval が組み込み関数から除去される"""
        executor = self._make_executor()
        with pytest.raises(NameError):
            executor.execute("eval('1+1')", {}, {})

    def test_blocks_os_import(self):
        """os モジュールのインポートが禁止される"""
        executor = self._make_executor()
        with pytest.raises(ImportError, match="許可されていません"):
            executor.execute("import os", {}, {})

    def test_blocks_subprocess_import(self):
        """subprocess モジュールのインポートが禁止される"""
        executor = self._make_executor()
        with pytest.raises(ImportError, match="許可されていません"):
            executor.execute("import subprocess", {}, {})

    def test_blocks_socket_import(self):
        """socket モジュールのインポートが禁止される"""
        executor = self._make_executor()
        with pytest.raises(ImportError, match="許可されていません"):
            executor.execute("import socket", {}, {})

    def test_blocks_sys_import(self):
        """sys モジュールのインポートが禁止される"""
        executor = self._make_executor()
        with pytest.raises(ImportError, match="許可されていません"):
            executor.execute("import sys", {}, {})

    def test_blocks_http_import(self):
        """http モジュールのインポートが禁止される"""
        executor = self._make_executor()
        with pytest.raises(ImportError, match="許可されていません"):
            executor.execute("import http.client", {}, {})

    def test_blocks_pickle_import(self):
        """pickle モジュールのインポートが禁止される"""
        executor = self._make_executor()
        with pytest.raises(ImportError, match="許可されていません"):
            executor.execute("import pickle", {}, {})

    def test_blocks_ctypes_import(self):
        """ctypes モジュールのインポートが禁止される"""
        executor = self._make_executor()
        with pytest.raises(ImportError, match="許可されていません"):
            executor.execute("import ctypes", {}, {})

    def test_syntax_error_raised(self):
        """構文エラーがSyntaxErrorとして伝播する"""
        executor = self._make_executor()
        with pytest.raises(SyntaxError):
            executor.execute("def foo(", {}, {})

    def test_safe_builtins_available(self):
        """安全な組み込み関数が利用可能"""
        executor = self._make_executor()
        code = """
result = {
    'len': len([1, 2, 3]),
    'range': list(range(3)),
    'sorted': sorted([3, 1, 2]),
    'sum': sum([1, 2, 3]),
}
"""
        result = executor.execute(code, {}, {})
        assert result["result"]["len"] == 3
        assert result["result"]["range"] == [0, 1, 2]
        assert result["result"]["sorted"] == [1, 2, 3]
        assert result["result"]["sum"] == 6

    def test_allowed_modules_work(self):
        """許可されたモジュール (math, json等) が使用可能"""
        executor = self._make_executor()
        code = "import math\nresult = math.sqrt(4)"
        result = executor.execute(code, {}, {})
        assert result["result"] == 2.0

    def test_blocks_submodule_of_blocked(self):
        """ブロックされたモジュールのサブモジュールもブロック"""
        executor = self._make_executor()
        with pytest.raises(ImportError, match="許可されていません"):
            executor.execute("import os.path", {}, {})
