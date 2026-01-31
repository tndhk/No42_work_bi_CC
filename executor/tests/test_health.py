import pytest
from fastapi.testclient import TestClient


def test_health_endpoint_returns_200():
    """ヘルスエンドポイントが200を返す"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint_structure():
    """ヘルスエンドポイントのレスポンス構造が正しい"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    json_data = response.json()
    assert "status" in json_data
    assert isinstance(json_data["status"], str)
