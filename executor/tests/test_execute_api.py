"""Executor API テスト"""
import pytest
from fastapi.testclient import TestClient


def test_execute_card_simple():
    """シンプルなカード実行が成功する"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/card", json={
        "card_id": "card_001",
        "code": 'def render(dataset, filters, params):\n    return "<div>Hello</div>"',
        "dataset_id": "ds_001",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["html"] == "<div>Hello</div>"
    assert "execution_time_ms" in data


def test_execute_card_with_dataset():
    """データ付きのカード実行"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/card", json={
        "card_id": "card_002",
        "code": 'def render(dataset, filters, params):\n    return f"<div>Rows: {len(dataset)}</div>"',
        "dataset_id": "ds_001",
        "dataset_rows": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ],
    })

    assert response.status_code == 200
    assert "Rows: 2" in response.json()["html"]


def test_execute_card_no_render_function():
    """render関数未定義で400エラー"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/card", json={
        "card_id": "card_003",
        "code": "x = 42",
        "dataset_id": "ds_001",
    })

    assert response.status_code == 400


def test_execute_card_syntax_error():
    """構文エラーで400エラー"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/card", json={
        "card_id": "card_004",
        "code": "def render(",
        "dataset_id": "ds_001",
    })

    assert response.status_code == 400


def test_execute_card_blocked_import():
    """ブロックされたモジュールのインポートで400エラー"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/card", json={
        "card_id": "card_005",
        "code": 'import os\ndef render(dataset, filters, params):\n    return "<div></div>"',
        "dataset_id": "ds_001",
    })

    assert response.status_code == 400


def test_execute_card_with_filters():
    """フィルタ付きのカード実行"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/card", json={
        "card_id": "card_006",
        "code": 'def render(dataset, filters, params):\n    return f"<div>{filters.get(\'cat\', \'none\')}</div>"',
        "dataset_id": "ds_001",
        "filters": {"cat": "Electronics"},
    })

    assert response.status_code == 200
    assert "Electronics" in response.json()["html"]


def test_health_still_works():
    """ヘルスエンドポイントが引き続き動作する"""
    from app.main import app
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Transform API Tests

def test_execute_transform_simple():
    """シンプルなTransform実行が成功する"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/transform", json={
        "transform_id": "tf_001",
        "code": "def transform(inputs, params):\n    return inputs['dataset1']",
        "input_datasets": {
            "dataset1": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
        },
    })

    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 2
    assert set(data["column_names"]) == {"name", "age"}
    assert len(data["output_rows"]) == 2
    assert "execution_time_ms" in data


def test_execute_transform_with_transformation():
    """Transform関数でDataFrameを加工できる"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/transform", json={
        "transform_id": "tf_002",
        "code": "def transform(inputs, params):\n    df = inputs['data'].copy()\n    df['doubled'] = df['value'] * 2\n    return df",
        "input_datasets": {
            "data": [
                {"value": 10},
                {"value": 20},
            ]
        },
    })

    assert response.status_code == 200
    data = response.json()
    assert "doubled" in data["column_names"]
    assert data["output_rows"][0]["doubled"] == 20
    assert data["output_rows"][1]["doubled"] == 40


def test_execute_transform_multiple_inputs():
    """複数入力データセットのTransform実行"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/transform", json={
        "transform_id": "tf_003",
        "code": """def transform(inputs, params):
    df1 = inputs['sales']
    df2 = inputs['products']
    return df1.merge(df2, on='product_id')
""",
        "input_datasets": {
            "sales": [
                {"product_id": 1, "quantity": 10},
                {"product_id": 2, "quantity": 20},
            ],
            "products": [
                {"product_id": 1, "name": "A"},
                {"product_id": 2, "name": "B"},
            ]
        },
    })

    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 2
    assert "quantity" in data["column_names"]
    assert "name" in data["column_names"]


def test_execute_transform_with_params():
    """params付きのTransform実行"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/transform", json={
        "transform_id": "tf_004",
        "code": "def transform(inputs, params):\n    df = inputs['data'].copy()\n    df['result'] = df['value'] * params.get('multiplier', 1)\n    return df",
        "input_datasets": {
            "data": [{"value": 5}]
        },
        "params": {"multiplier": 3},
    })

    assert response.status_code == 200
    data = response.json()
    assert data["output_rows"][0]["result"] == 15


def test_execute_transform_no_transform_function():
    """transform関数未定義で400エラー"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/transform", json={
        "transform_id": "tf_005",
        "code": "x = 42",
        "input_datasets": {"data": [{"a": 1}]},
    })

    assert response.status_code == 400


def test_execute_transform_invalid_return():
    """transform関数がDataFrameでない値を返すと400エラー"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/transform", json={
        "transform_id": "tf_006",
        "code": "def transform(inputs, params):\n    return 'not a dataframe'",
        "input_datasets": {"data": [{"a": 1}]},
    })

    assert response.status_code == 400


def test_execute_transform_blocked_import():
    """ブロックされたモジュールのインポートで400エラー"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/transform", json={
        "transform_id": "tf_007",
        "code": "import os\ndef transform(inputs, params):\n    return inputs['data']",
        "input_datasets": {"data": [{"a": 1}]},
    })

    assert response.status_code == 400


def test_execute_transform_syntax_error():
    """構文エラーで400エラー"""
    from app.main import app
    client = TestClient(app)

    response = client.post("/execute/transform", json={
        "transform_id": "tf_008",
        "code": "def transform(",
        "input_datasets": {"data": [{"a": 1}]},
    })

    assert response.status_code == 400
