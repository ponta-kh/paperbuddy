import logging
from uuid import UUID

import pytest

from src.application.use_cases.chat.delete_chat.delete_chat import DeleteChatUseCase
from src.application.use_cases.chat.delete_chat.delete_chat_dto import DeleteChatInput

CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000001")
REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")


class StubChatRepository:
    def __init__(self) -> None:
        self.deleted_chat_id: UUID | None = None

    async def delete_chat(self, *, chat_id: UUID, user_id: UUID) -> None:
        self.deleted_chat_id = chat_id
        self.deleted_user_id = user_id


class FailingChatRepository:
    async def delete_chat(self, *, chat_id: UUID, user_id: UUID) -> None:
        raise RuntimeError("DynamoDB failure")


@pytest.mark.asyncio
async def test_delete_chat_deletes_items_for_chat_id() -> None:
    repository = StubChatRepository()

    await DeleteChatUseCase(repository).execute(
        DeleteChatInput(chat_id=CHAT_ID, user_id=USER_ID, request_id=REQUEST_ID)
    )

    assert repository.deleted_chat_id == CHAT_ID
    assert repository.deleted_user_id == USER_ID


@pytest.mark.asyncio
async def test_delete_chat_logs_repository_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with (
        caplog.at_level(
            logging.ERROR,
            logger="src.application.use_cases.chat.delete_chat.delete_chat",
        ),
        pytest.raises(RuntimeError, match="DynamoDB failure"),
    ):
        await DeleteChatUseCase(FailingChatRepository()).execute(
            DeleteChatInput(chat_id=CHAT_ID, user_id=USER_ID, request_id=REQUEST_ID)
        )

    record = caplog.records[0]
    assert getattr(record, "event") == "delete_chat_failed"
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert getattr(record, "chat_id") == str(CHAT_ID)
