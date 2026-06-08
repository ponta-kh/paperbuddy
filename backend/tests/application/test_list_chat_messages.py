from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.chat import ChatMessageRecord
from src.application.use_cases.chat.list_chat_messages.list_chat_messages import (
    ListChatMessagesUseCase,
)
from src.application.use_cases.chat.list_chat_messages.list_chat_messages_dto import (
    ListChatMessagesInput,
)


USER_ID = UUID("00000000-0000-0000-0000-000000000001")
CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")


class StubChatQueryRepository:
    def __init__(self, messages: tuple[ChatMessageRecord, ...] | None) -> None:
        self.messages = messages
        self.received: tuple[UUID, UUID] | None = None

    async def list_messages_by_chat_id(
        self,
        *,
        user_id: UUID,
        chat_id: UUID,
    ) -> tuple[ChatMessageRecord, ...]:
        self.received = (user_id, chat_id)
        if self.messages is None:
            raise RepositoryNotFoundError
        return self.messages


@pytest.mark.asyncio
async def test_list_chat_messages_returns_repository_results() -> None:
    turn_id = UUID("00000000-0000-0000-0000-000000000010")
    sent_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    repository = StubChatQueryRepository(
        (ChatMessageRecord(turn_id, "user", "question", sent_at),)
    )

    output = await ListChatMessagesUseCase(repository).execute(
        ListChatMessagesInput(user_id=USER_ID, chat_id=CHAT_ID)
    )

    assert repository.received == (USER_ID, CHAT_ID)
    assert output.chat_id == CHAT_ID
    assert output.messages[0].turn_id == turn_id
    assert output.messages[0].content == "question"


@pytest.mark.asyncio
async def test_list_chat_messages_propagates_not_found() -> None:
    repository = StubChatQueryRepository(None)

    with pytest.raises(RepositoryNotFoundError):
        await ListChatMessagesUseCase(repository).execute(
            ListChatMessagesInput(user_id=USER_ID, chat_id=CHAT_ID)
        )


@pytest.mark.parametrize("chat_id", ["", "not-a-uuid", 1])
def test_list_chat_messages_input_rejects_invalid_chat_id(chat_id: object) -> None:
    with pytest.raises(ValidationError):
        ListChatMessagesInput(user_id=USER_ID, chat_id=chat_id)
