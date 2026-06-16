import json
import logging
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from src.dependencies.logging_config import JsonLogFormatter, set_log_context
from src.presentation import request_id as request_id_module
from src.presentation.access_log import register_access_log_middleware
from src.presentation.auth import AuthenticatedUser

REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_access_log_outputs_success_log(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(request_id_module, "uuid7", lambda: REQUEST_ID)
    app = _create_test_app()
    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="src.presentation.access_log"):
        response = client.get("/health")

    assert response.status_code == 200
    payload = _access_log_payload(caplog)
    assert payload["message"] == "HTTPリクエストを処理しました"
    assert payload["event"] == "http_request"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert payload["request_id"] == str(REQUEST_ID)
    assert isinstance(payload["duration_ms"], int)


def test_access_log_outputs_user_id_when_authenticated(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(request_id_module, "uuid7", lambda: REQUEST_ID)
    app = _create_test_app()
    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="src.presentation.access_log"):
        response = client.get("/private")

    assert response.status_code == 200
    payload = _access_log_payload(caplog)
    assert payload["user_id"] == str(USER_ID)


def _create_test_app() -> FastAPI:
    app = FastAPI()
    register_access_log_middleware(app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/private")
    async def private(
        user: AuthenticatedUser = Depends(_authenticated_user),
    ) -> dict[str, str]:
        return {"user_id": str(user.user_id)}

    return app


def _authenticated_user(request: Request) -> AuthenticatedUser:
    request.state.user_id = USER_ID
    set_log_context(user_id=USER_ID)
    return AuthenticatedUser(user_id=USER_ID)


def _access_log_payload(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    formatter = JsonLogFormatter()
    records = [
        record
        for record in caplog.records
        if record.name == "src.presentation.access_log"
    ]
    assert len(records) == 1
    return json.loads(formatter.format(records[0]))
