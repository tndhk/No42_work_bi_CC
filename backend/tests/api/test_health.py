"""Health endpoint test following TDD RED phase."""
from fastapi.testclient import TestClient


def test_health_endpoint_returns_200():
    """ヘルスエンドポイントが200を返す."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
