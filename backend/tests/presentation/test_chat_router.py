from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from main import app
from src.application.exceptions import (
    ChatContinuationExpiredError,
    RepositoryAccessError,
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
from src.application.use_cases.chat.rename_chat.rename_chat_dto import RenameChatOutput
from src.application.use_cases.chat.start_chat.start_chat_dto import StartChatOutput
from src.dependencies.chat_deps import (
    get_continue_chat_use_case,
    get_delete_chat_use_case,
    get_list_chat_messages_use_case,
    get_list_chats_use_case,
    get_rename_chat_use_case,
    get_start_chat_use_case,
)
from src.domain.repositories.chat_command_repository_protocol import ChatConflictError
from src.presentation.auth import AuthenticatedUser, get_authenticated_user

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
CHAT_ID_TEXT = str(CHAT_ID)


class StubStartChatUseCase:
    async def execute(self, command: object) -> StartChatOutput:
        assert command.user_id == UUID("00000000-0000-0000-0000-000000000001")
        assert command.prompt == "question"
        return StartChatOutput(chat_id=CHAT_ID, answer="answer", title="title")


class StubContinueChatUseCase:
    async def execute(self, command: object) -> ContinueChatOutput:
        assert command.user_id == UUID("00000000-0000-0000-0000-000000000001")
        assert command.chat_id == CHAT_ID
        assert command.prompt == "next question"
        return ContinueChatOutput(chat_id=CHAT_ID, answer="next answer", title="title")


class StubRenameChatUseCase:
    async def execute(self, command: object) -> RenameChatOutput:
        assert command.user_id == UUID("00000000-0000-0000-0000-000000000001")
        assert command.chat_id == CHAT_ID
        assert command.title == "変更後"
        return RenameChatOutput(chat_id=CHAT_ID, title="変更後")


class StubDeleteChatUseCase:
    def __init__(self) -> None:
        self.called = False

    async def execute(self, command: object) -> None:
        assert command.chat_id == CHAT_ID
        assert command.user_id == USER_ID
        self.called = True


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
                    chat_id=CHAT_ID,
                    title="title",
                    created_at=created_at,
                    last_updated_at=created_at,
                ),
            )
        )


class StubListChatMessagesUseCase:
    async def execute(self, query: object) -> ListChatMessagesOutput:
        assert query.user_id == UUID("00000000-0000-0000-0000-000000000001")
        assert query.chat_id == CHAT_ID
        return ListChatMessagesOutput(
            chat_id=CHAT_ID,
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


class StubUnavailableListChatsUseCase:
    async def execute(self, query: object) -> ListChatsOutput:
        raise RepositoryAccessError


def test_list_chats_endpoint() -> None:
    app.dependency_overrides[get_list_chats_use_case] = lambda: StubListChatsUseCase()
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.get(
        "/api/chats",
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "chats": [
            {
                "chat_id": CHAT_ID_TEXT,
                "title": "title",
                "created_at": "2026-01-01T00:00:00Z",
                "last_updated_at": "2026-01-01T00:00:00Z",
            }
        ]
    }


def test_list_chats_endpoint_returns_service_unavailable_for_repository_error() -> None:
    app.dependency_overrides[get_list_chats_use_case] = lambda: (
        StubUnavailableListChatsUseCase()
    )
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.get(
        "/api/chats",
    )

    app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["code"] == "repository_unavailable"


def test_list_chat_messages_endpoint() -> None:
    app.dependency_overrides[get_list_chat_messages_use_case] = lambda: (
        StubListChatMessagesUseCase()
    )
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.get(
        f"/api/chats/{CHAT_ID_TEXT}/messages",
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "chat_id": CHAT_ID_TEXT,
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
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.get(
        f"/api/chats/{CHAT_ID_TEXT}/messages",
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert response.json()["code"] == "chat_not_found"


def test_continue_chat_endpoint() -> None:
    app.dependency_overrides[get_continue_chat_use_case] = lambda: (
        StubContinueChatUseCase()
    )
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.post(
        f"/api/chats/{CHAT_ID_TEXT}/messages",
        json={"prompt": "next question"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "chat_id": CHAT_ID_TEXT,
        "answer": "next answer",
        "title": "title",
    }


def test_rename_chat_endpoint() -> None:
    app.dependency_overrides[get_rename_chat_use_case] = lambda: StubRenameChatUseCase()
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.patch(
        f"/api/chats/{CHAT_ID_TEXT}",
        json={"title": "変更後"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"chat_id": CHAT_ID_TEXT, "title": "変更後"}


def test_delete_chat_endpoint() -> None:
    use_case = StubDeleteChatUseCase()
    app.dependency_overrides[get_delete_chat_use_case] = lambda: use_case
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.delete(
        f"/api/chats/{CHAT_ID_TEXT}",
    )

    app.dependency_overrides.clear()
    assert response.status_code == 204
    assert response.content == b""
    assert use_case.called


def test_continue_chat_endpoint_returns_conflict_when_expired() -> None:
    app.dependency_overrides[get_continue_chat_use_case] = lambda: (
        StubExpiredContinueChatUseCase()
    )
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.post(
        f"/api/chats/{CHAT_ID_TEXT}/messages",
        json={"prompt": "next question"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409
    assert response.json()["code"] == "chat_continuation_expired"


def test_continue_chat_endpoint_returns_conflict_when_stale() -> None:
    app.dependency_overrides[get_continue_chat_use_case] = lambda: (
        StubConflictContinueChatUseCase()
    )
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.post(
        f"/api/chats/{CHAT_ID_TEXT}/messages",
        json={"prompt": "next question"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409
    assert response.json()["code"] == "chat_conflict"


def test_start_chat_endpoint() -> None:
    app.dependency_overrides[get_start_chat_use_case] = lambda: StubStartChatUseCase()
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.post(
        "/api/chats",
        json={"prompt": "question"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json() == {
        "chat_id": CHAT_ID_TEXT,
        "answer": "answer",
        "title": "title",
    }


def test_start_chat_endpoint_rejects_missing_authentication() -> None:
    client = TestClient(app)

    response = client.post("/api/chats", json={"prompt": "question"})

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_failed"
