import logging
from uuid import UUID

import pytest

from src.application.use_cases.chat.rename_chat.rename_chat import RenameChatUseCase
from src.application.use_cases.chat.rename_chat.rename_chat_dto import RenameChatInput

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")


class StubChatRepository:
    def __init__(self) -> None:
        self.updated: tuple[UUID, UUID, str] | None = None

    async def update_title(
        self,
        *,
        chat_id: UUID,
        user_id: UUID,
        title: str,
    ) -> None:
        self.updated = (chat_id, user_id, title)


class FailingChatRepository:
    async def update_title(
        self,
        *,
        chat_id: UUID,
        user_id: UUID,
        title: str,
    ) -> None:
        raise RuntimeError("DynamoDB failure")


@pytest.mark.asyncio
async def test_rename_chat_updates_title_and_returns_result() -> None:
    repository = StubChatRepository()

    output = await RenameChatUseCase(repository).execute(
        RenameChatInput(
            user_id=USER_ID,
            chat_id=CHAT_ID,
            title="変更後",
            request_id=REQUEST_ID,
        )
    )

    assert repository.updated == (CHAT_ID, USER_ID, "変更後")
    assert output.chat_id == CHAT_ID
    assert output.title == "変更後"


@pytest.mark.asyncio
async def test_rename_chat_logs_repository_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with (
        caplog.at_level(
            logging.ERROR,
            logger="src.application.use_cases.chat.rename_chat.rename_chat",
        ),
        pytest.raises(RuntimeError, match="DynamoDB failure"),
    ):
        await RenameChatUseCase(FailingChatRepository()).execute(
            RenameChatInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                title="変更後",
                request_id=REQUEST_ID,
            )
        )

    record = caplog.records[0]
    assert getattr(record, "event") == "rename_chat_failed"
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert getattr(record, "chat_id") == str(CHAT_ID)
