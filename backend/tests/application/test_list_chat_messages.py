from datetime import datetime, timezone
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.chat import ChatMessageRecord, ChatSummary
from src.application.use_cases.chat.list_chat_messages.list_chat_messages import (
    ListChatMessagesUseCase,
)
from src.application.use_cases.chat.list_chat_messages.list_chat_messages_dto import (
    ListChatMessagesInput,
)
from src.domain.entities.chat.chat import ChatCitation, ChatCitationSource

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")
_CITATION_METADATA: dict[str, object] = {"title": "paper", "page": 3}
CITATIONS = (
    ChatCitation(
        text="answer",
        span_start=0,
        span_end=6,
        sources=(
            ChatCitationSource(
                content="source excerpt",
                location_type="S3",
                uri="s3://bucket/paper.pdf",
                metadata=_CITATION_METADATA,
            ),
        ),
    ),
)


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

    async def list_chats_by_user_id(self, user_id: UUID) -> tuple[ChatSummary, ...]:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_list_chat_messages_returns_repository_results() -> None:
    message_request_id = UUID("00000000-0000-0000-0000-000000000010")
    sent_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    repository = StubChatQueryRepository(
        (
            ChatMessageRecord(
                message_request_id,
                "llm",
                "answer",
                sent_at,
                citations=CITATIONS,
            ),
        )
    )

    output = await ListChatMessagesUseCase(repository).execute(
        ListChatMessagesInput(
            user_id=USER_ID,
            chat_id=CHAT_ID,
            request_id=REQUEST_ID,
        )
    )

    assert repository.received == (USER_ID, CHAT_ID)
    assert output.chat_id == CHAT_ID
    assert output.messages[0].request_id == message_request_id
    assert output.messages[0].content == "answer"
    assert output.messages[0].citations == CITATIONS


@pytest.mark.asyncio
async def test_list_chat_messages_propagates_not_found() -> None:
    repository = StubChatQueryRepository(None)

    with pytest.raises(RepositoryNotFoundError):
        await ListChatMessagesUseCase(repository).execute(
            ListChatMessagesInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                request_id=REQUEST_ID,
            )
        )


@pytest.mark.parametrize("chat_id", ["", "not-a-uuid", 1])
def test_list_chat_messages_input_rejects_invalid_chat_id(chat_id: object) -> None:
    with pytest.raises(ValidationError):
        ListChatMessagesInput(
            user_id=USER_ID,
            chat_id=cast(UUID, chat_id),
            request_id=REQUEST_ID,
        )
