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
