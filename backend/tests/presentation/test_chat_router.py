from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from main import app
from src.application.exceptions import (
    ChatContinuationExpiredError,
    RepositoryNotFoundError,
)
from src.application.use_cases.chat.continue_chat.continue_chat_dto import (
    ContinueChatOutput,
)
from src.application.use_cases.chat.list_chat_messages.list_chat_messages_dto import (
    ChatMessageOutput,
    ListChatMessagesOutput,
)
from src.application.use_cases.chat.list_chats.list_chats_dto import (
    ChatSummaryOutput,
    ListChatsOutput,
)
from src.application.use_cases.chat.start_chat.start_chat_dto import StartChatOutput
from src.dependencies.chat_deps import (
    get_continue_chat_use_case,
    get_list_chat_messages_use_case,
    get_list_chats_use_case,
    get_start_chat_use_case,
)
from src.domain.repositories.chat_command_repository_protocol import ChatConflictError


class StubStartChatUseCase:
    async def execute(self, command: object) -> StartChatOutput:
        assert command.user_id == UUID("00000000-0000-0000-0000-000000000001")
        assert command.prompt == "question"
        return StartChatOutput(chat_id="session-1", answer="answer", title="title")


class StubContinueChatUseCase:
    async def execute(self, command: object) -> ContinueChatOutput:
        assert command.user_id == UUID("00000000-0000-0000-0000-000000000001")
        assert command.chat_id == "session-1"
        assert command.prompt == "next question"
        return ContinueChatOutput(
            chat_id="session-1", answer="next answer", title="title"
        )


class StubExpiredContinueChatUseCase:
    async def execute(self, command: object) -> ContinueChatOutput:
        raise ChatContinuationExpiredError


class StubConflictContinueChatUseCase:
    async def execute(self, command: object) -> ContinueChatOutput:
        raise ChatConflictError


class StubListChatsUseCase:
    async def execute(self, query: object) -> ListChatsOutput:
        assert query.user_id == UUID("00000000-0000-0000-0000-000000000001")
        created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return ListChatsOutput(
            chats=(
                ChatSummaryOutput(
                    chat_id="session-1",
                    title="title",
                    created_at=created_at,
                    last_updated_at=created_at,
                ),
            )
        )


class StubListChatMessagesUseCase:
    async def execute(self, query: object) -> ListChatMessagesOutput:
        assert query.user_id == UUID("00000000-0000-0000-0000-000000000001")
        assert query.chat_id == "session-1"
        return ListChatMessagesOutput(
            chat_id="session-1",
            messages=(
                ChatMessageOutput(
                    turn_id=UUID("00000000-0000-0000-0000-000000000010"),
                    sender="user",
                    content="question",
                    sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
            ),
        )


class StubNotFoundListChatMessagesUseCase:
    async def execute(self, query: object) -> ListChatMessagesOutput:
        raise RepositoryNotFoundError


def test_list_chats_endpoint() -> None:
    app.dependency_overrides[get_list_chats_use_case] = lambda: StubListChatsUseCase()
    client = TestClient(app)

    response = client.get(
        "/chats",
        headers={"X-User-ID": "00000000-0000-0000-0000-000000000001"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "chats": [
            {
                "chat_id": "session-1",
                "title": "title",
                "created_at": "2026-01-01T00:00:00Z",
                "last_updated_at": "2026-01-01T00:00:00Z",
            }
        ]
    }


def test_list_chat_messages_endpoint() -> None:
    app.dependency_overrides[get_list_chat_messages_use_case] = lambda: (
        StubListChatMessagesUseCase()
    )
    client = TestClient(app)

    response = client.get(
        "/chats/session-1/messages",
        headers={"X-User-ID": "00000000-0000-0000-0000-000000000001"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "chat_id": "session-1",
        "messages": [
            {
                "turn_id": "00000000-0000-0000-0000-000000000010",
                "sender": "user",
                "content": "question",
                "sent_at": "2026-01-01T00:00:00Z",
            }
        ],
    }


def test_list_chat_messages_endpoint_returns_not_found() -> None:
    app.dependency_overrides[get_list_chat_messages_use_case] = lambda: (
        StubNotFoundListChatMessagesUseCase()
    )
    client = TestClient(app)

    response = client.get(
        "/chats/missing/messages",
        headers={"X-User-ID": "00000000-0000-0000-0000-000000000001"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert response.json()["code"] == "chat_not_found"


def test_continue_chat_endpoint() -> None:
    app.dependency_overrides[get_continue_chat_use_case] = lambda: (
        StubContinueChatUseCase()
    )
    client = TestClient(app)

    response = client.post(
        "/chats/session-1/messages",
        headers={"X-User-ID": "00000000-0000-0000-0000-000000000001"},
        json={"prompt": "next question"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "chat_id": "session-1",
        "answer": "next answer",
        "title": "title",
    }


def test_continue_chat_endpoint_returns_conflict_when_expired() -> None:
    app.dependency_overrides[get_continue_chat_use_case] = lambda: (
        StubExpiredContinueChatUseCase()
    )
    client = TestClient(app)

    response = client.post(
        "/chats/session-1/messages",
        headers={"X-User-ID": "00000000-0000-0000-0000-000000000001"},
        json={"prompt": "next question"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409
    assert response.json()["code"] == "chat_continuation_expired"


def test_continue_chat_endpoint_returns_conflict_when_stale() -> None:
    app.dependency_overrides[get_continue_chat_use_case] = lambda: (
        StubConflictContinueChatUseCase()
    )
    client = TestClient(app)

    response = client.post(
        "/chats/session-1/messages",
        headers={"X-User-ID": "00000000-0000-0000-0000-000000000001"},
        json={"prompt": "next question"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409
    assert response.json()["code"] == "chat_conflict"


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
