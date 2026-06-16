import logging
from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.chat import ChatSummary
from src.application.use_cases.chat.list_chats.list_chats import ListChatsUseCase
from src.application.use_cases.chat.list_chats.list_chats_dto import ListChatsInput

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")


class StubChatQueryRepository:
    def __init__(self, chats: tuple[ChatSummary, ...] | None) -> None:
        self.chats = chats
        self.user_id: UUID | None = None

    async def list_chats_by_user_id(self, user_id: UUID) -> tuple[ChatSummary, ...]:
        self.user_id = user_id
        if self.chats is None:
            raise RepositoryNotFoundError
        return self.chats


@pytest.mark.asyncio
async def test_list_chats_returns_repository_results() -> None:
    updated_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
    repository = StubChatQueryRepository(
        (
            ChatSummary(
                chat_id=CHAT_ID,
                title="title",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                last_updated_at=updated_at,
            ),
        )
    )

    output = await ListChatsUseCase(repository).execute(
        ListChatsInput(user_id=USER_ID, request_id=REQUEST_ID)
    )

    assert repository.user_id == USER_ID
    assert output.chats[0].chat_id == CHAT_ID
    assert output.chats[0].last_updated_at == updated_at


@pytest.mark.asyncio
async def test_list_chats_converts_not_found_to_empty_list() -> None:
    repository = StubChatQueryRepository(None)

    output = await ListChatsUseCase(repository).execute(
        ListChatsInput(user_id=USER_ID, request_id=REQUEST_ID)
    )

    assert output.chats == ()


@pytest.mark.asyncio
async def test_list_chats_logs_not_found(
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository = StubChatQueryRepository(None)

    with caplog.at_level(
        logging.WARNING,
        logger="src.application.use_cases.chat.list_chats.list_chats",
    ):
        await ListChatsUseCase(repository).execute(
            ListChatsInput(user_id=USER_ID, request_id=REQUEST_ID)
        )

    record = caplog.records[0]
    assert record.event == "list_chats_not_found"
    assert record.request_id == str(REQUEST_ID)
    assert record.user_id == str(USER_ID)
