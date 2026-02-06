"""TransformRunner テスト"""
import pytest
import pandas as pd


class TestTransformResult:
    """TransformResult のテスト"""

    def test_create_with_df_and_time(self):
        """DataFrameと実行時間を保持できる"""
        from app.transform_runner import TransformResult

        df = pd.DataFrame({'a': [1, 2, 3]})
        result = TransformResult(df=df, execution_time_ms=123.45)

        assert result.df.equals(df)
        assert result.execution_time_ms == 123.45


class TestTransformRunner:
    """TransformRunner のテスト"""

    def _make_runner(self, **kwargs):
        from app.transform_runner import TransformRunner
        return TransformRunner(**kwargs)

    def _make_input_df(self):
        return pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'category': ['A', 'B', 'A'],
            'amount': [100, 200, 300],
        })

    def test_execute_simple_transform(self):
        """transform関数がDataFrameを返せる"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    df = inputs['dataset1']
    return df
"""
        inputs = {'dataset1': self._make_input_df()}
        result = runner.execute(code, inputs, {})

        assert isinstance(result.df, pd.DataFrame)
        assert len(result.df) == 3
        assert result.execution_time_ms > 0

    def test_execute_with_transformation(self):
        """transform関数でDataFrameを加工できる"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    df = inputs['dataset1'].copy()
    df['doubled'] = df['amount'] * 2
    return df
"""
        inputs = {'dataset1': self._make_input_df()}
        result = runner.execute(code, inputs, {})

        assert 'doubled' in result.df.columns
        assert list(result.df['doubled']) == [200, 400, 600]

    def test_execute_with_multiple_inputs(self):
        """複数の入力データセットを処理できる"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    df1 = inputs['sales']
    df2 = inputs['products']
    merged = df1.merge(df2, on='product_id')
    return merged
"""
        sales_df = pd.DataFrame({
            'product_id': [1, 2, 3],
            'quantity': [10, 20, 30],
        })
        products_df = pd.DataFrame({
            'product_id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
        })
        inputs = {'sales': sales_df, 'products': products_df}
        result = runner.execute(code, inputs, {})

        assert 'quantity' in result.df.columns
        assert 'name' in result.df.columns
        assert len(result.df) == 3

    def test_execute_with_params(self):
        """paramsがtransform関数に渡される"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    df = inputs['dataset1'].copy()
    multiplier = params.get('multiplier', 1)
    df['result'] = df['amount'] * multiplier
    return df
"""
        inputs = {'dataset1': self._make_input_df()}
        result = runner.execute(code, inputs, {'multiplier': 3})

        assert list(result.df['result']) == [300, 600, 900]

    def test_execute_without_transform_raises(self):
        """transform関数未定義でValueError"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def some_other_func():
    pass
"""
        with pytest.raises(ValueError, match="コードには 'transform' 関数または 'result' 変数が必要です"):
            runner.execute(code, {'dataset1': self._make_input_df()}, {})

    def test_execute_invalid_return_type_raises(self):
        """transform関数がDataFrameでない型を返すとValueError"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    return "not a dataframe"
"""
        with pytest.raises(ValueError, match="DataFrameを返す必要があります"):
            runner.execute(code, {'dataset1': self._make_input_df()}, {})

    def test_execute_return_none_raises(self):
        """transform関数がNoneを返すとValueError"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    return None
"""
        with pytest.raises(ValueError, match="DataFrameを返す必要があります"):
            runner.execute(code, {'dataset1': self._make_input_df()}, {})

    def test_timeout_raises_error(self):
        """タイムアウト超過でTimeoutError"""
        runner = self._make_runner(timeout_seconds=1)
        code = """
def transform(inputs, params):
    while True:
        pass
    return inputs['dataset1']
"""
        with pytest.raises(TimeoutError):
            runner.execute(code, {'dataset1': self._make_input_df()}, {})

    def test_blocked_imports_in_transform(self):
        """transform関数内でブロックされたモジュールを使えない"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    import os
    return inputs['dataset1']
"""
        with pytest.raises(ImportError, match="許可されていません"):
            runner.execute(code, {'dataset1': self._make_input_df()}, {})

    def test_default_timeout_and_memory(self):
        """デフォルトのtimeout=300秒, memory=4096MB"""
        runner = self._make_runner()
        assert runner._limiter.timeout == 300
        assert runner._limiter.max_memory == 4096 * 1024 * 1024

    def test_execute_with_pandas_operations(self):
        """transform関数内でpandas操作が可能"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    df = inputs['dataset1']
    result = df.groupby('category').agg({'amount': 'sum'}).reset_index()
    return result
"""
        inputs = {'dataset1': self._make_input_df()}
        result = runner.execute(code, inputs, {})

        assert len(result.df) == 2  # categories A and B
        assert 'amount' in result.df.columns

    def test_execute_with_numpy_operations(self):
        """transform関数内でnumpy操作が可能"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    df = inputs['dataset1'].copy()
    df['log_amount'] = np.log(df['amount'])
    return df
"""
        inputs = {'dataset1': self._make_input_df()}
        result = runner.execute(code, inputs, {})

        assert 'log_amount' in result.df.columns

    def test_execute_empty_inputs_dict(self):
        """空の入力辞書でも動作する"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    return pd.DataFrame({'result': [1, 2, 3]})
"""
        result = runner.execute(code, {}, {})

        assert list(result.df['result']) == [1, 2, 3]


class TestTransformRunnerInlineStyle:
    """inline スタイル（transform関数なし）のテスト"""

    def _make_runner(self, **kwargs):
        from app.transform_runner import TransformRunner
        return TransformRunner(**kwargs)

    def _make_input_df(self):
        return pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'category': ['A', 'B', 'A'],
            'amount': [100, 200, 300],
        })

    def test_inline_style_params_accessible(self):
        """inlineスタイルでparamsにアクセスできる"""
        runner = self._make_runner(timeout_seconds=5)
        code = """
def transform(inputs, params):
    df = inputs['dataset1'].copy()
    multiplier = params.get('multiplier', 1)
    df['result'] = df['amount'] * multiplier
    result = df
    return result
"""
        # This works because params is passed as argument.
        # Now test that params is also available in global scope for inline code.
        inline_code = """
df_0 = inputs['dataset1'].copy()
multiplier = params.get('multiplier', 1)
df_0['result'] = df_0['amount'] * multiplier
result = df_0
"""
        inputs = {'dataset1': self._make_input_df()}
        result = runner.execute(inline_code, inputs, {'multiplier': 3})

        assert list(result.df['result']) == [300, 600, 900]

    def test_inline_style_inputs_accessible(self):
        """inlineスタイルでinputs辞書にアクセスできる"""
        runner = self._make_runner(timeout_seconds=5)
        inline_code = """
df = inputs['sales']
result = df[df['quantity'] > 15]
"""
        sales_df = pd.DataFrame({
            'product_id': [1, 2, 3],
            'quantity': [10, 20, 30],
        })
        inputs = {'sales': sales_df}
        result = runner.execute(inline_code, inputs, {})

        assert len(result.df) == 2
        assert list(result.df['quantity']) == [20, 30]

    def test_inline_style_df_0_accessible(self):
        """inlineスタイルでdf_0, df_1 にアクセスできる"""
        runner = self._make_runner(timeout_seconds=5)
        inline_code = """
result = pd.concat([df_0, df_1], ignore_index=True)
"""
        df_a = pd.DataFrame({'x': [1, 2]})
        df_b = pd.DataFrame({'x': [3, 4]})
        inputs = {'a': df_a, 'b': df_b}
        result = runner.execute(inline_code, inputs, {})

        assert len(result.df) == 4
        assert list(result.df['x']) == [1, 2, 3, 4]

    def test_inline_style_params_empty_dict(self):
        """inlineスタイルでparamsが空辞書でもアクセス可能"""
        runner = self._make_runner(timeout_seconds=5)
        inline_code = """
val = params.get('missing_key', 'default_value')
result = pd.DataFrame({'value': [val]})
"""
        inputs = {'dataset1': self._make_input_df()}
        result = runner.execute(inline_code, inputs, {})

        assert list(result.df['value']) == ['default_value']
