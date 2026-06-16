from uuid import UUID

from fastapi.testclient import TestClient

from main import app
from src.presentation.request_id import get_request_id


def test_health_endpoint_returns_ok_without_authentication() -> None:
    called = False

    def override_request_id() -> UUID:
        nonlocal called
        called = True
        return UUID("019ecde4-0000-7000-8000-000000000001")

    app.dependency_overrides[get_request_id] = override_request_id
    client = TestClient(app)

    response = client.get("/api/health")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert called
