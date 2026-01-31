"""CardRunner テスト"""
import pytest
import pandas as pd


class TestCardRunner:
    """CardRunner のテスト"""

    def _make_runner(self, **kwargs):
        from app.runner import CardRunner
        return CardRunner(**kwargs)

    def _make_df(self):
        return pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'category': ['A', 'B', 'A'],
            'amount': [100, 200, 300],
        })

    def test_execute_simple_render(self):
        """render関数がHTML文字列を返せる"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def render(dataset, filters, params):
    return "<div>Hello</div>"
"""
        result = runner.execute(code, self._make_df())
        assert result.html == "<div>Hello</div>"

    def test_execute_with_htmlresult(self):
        """render関数がHTMLResultを返せる"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def render(dataset, filters, params):
    return HTMLResult(
        html="<div>Chart</div>",
        used_columns=["date", "amount"],
        filter_applicable=["category"],
    )
"""
        result = runner.execute(code, self._make_df())
        assert result.html == "<div>Chart</div>"
        assert result.used_columns == ["date", "amount"]
        assert result.filter_applicable == ["category"]

    def test_execute_with_pandas(self):
        """render関数内でpandasが使用可能"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def render(dataset, filters, params):
    total = dataset['amount'].sum()
    return f"<div>Total: {total}</div>"
"""
        result = runner.execute(code, self._make_df())
        assert "600" in result.html

    def test_execute_without_render_raises(self):
        """render関数未定義でValueError"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def some_other_func():
    pass
"""
        with pytest.raises(ValueError, match="render関数が定義されていません"):
            runner.execute(code, self._make_df())

    def test_execute_invalid_return_type_raises(self):
        """render関数が不正な型を返すとValueError"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def render(dataset, filters, params):
    return 42
"""
        with pytest.raises(ValueError, match="str または HTMLResult"):
            runner.execute(code, self._make_df())

    def test_execute_with_filters(self):
        """filtersがrender関数に渡される"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def render(dataset, filters, params):
    cat = filters.get('category', 'ALL')
    return f"<div>Category: {cat}</div>"
"""
        result = runner.execute(code, self._make_df(), filters={'category': 'A'})
        assert "Category: A" in result.html

    def test_execute_with_params(self):
        """paramsがrender関数に渡される"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def render(dataset, filters, params):
    title = params.get('title', 'Default')
    return f"<div>{title}</div>"
"""
        result = runner.execute(code, self._make_df(), params={'title': 'My Chart'})
        assert "My Chart" in result.html

    def test_timeout_raises_error(self):
        """タイムアウト超過でTimeoutError"""
        runner = self._make_runner(timeout_seconds=1)
        code = """
def render(dataset, filters, params):
    while True:
        pass
    return "<div>Done</div>"
"""
        with pytest.raises(TimeoutError):
            runner.execute(code, self._make_df())

    def test_blocked_imports_in_render(self):
        """render関数内でブロックされたモジュールを使えない"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def render(dataset, filters, params):
    import os
    return "<div>hacked</div>"
"""
        with pytest.raises(ImportError, match="許可されていません"):
            runner.execute(code, self._make_df())
