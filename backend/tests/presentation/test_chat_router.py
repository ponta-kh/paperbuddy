from uuid import UUID

from fastapi.testclient import TestClient

from main import app
from src.application.use_cases.chat.start_chat.start_chat_dto import StartChatOutput
from src.dependencies.chat_deps import get_start_chat_use_case


class StubStartChatUseCase:
    async def execute(self, command: object) -> StartChatOutput:
        assert command.user_id == UUID("00000000-0000-0000-0000-000000000001")
        assert command.prompt == "question"
        return StartChatOutput(chat_id="session-1", answer="answer", title="title")


def test_start_chat_endpoint() -> None:
    app.dependency_overrides[get_start_chat_use_case] = lambda: StubStartChatUseCase()
    client = TestClient(app)

    response = client.post(
        "/chats",
        headers={"X-User-ID": "00000000-0000-0000-0000-000000000001"},
        json={"prompt": "question"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json() == {
        "chat_id": "session-1",
        "answer": "answer",
        "title": "title",
    }


def test_start_chat_endpoint_rejects_missing_authentication() -> None:
    client = TestClient(app)

    response = client.post("/chats", json={"prompt": "question"})

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_failed"
