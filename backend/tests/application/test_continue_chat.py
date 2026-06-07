from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.application.exceptions import ChatContinuationExpiredError
from src.application.ports.out.chat_generation_client_protocol import (
    ContinueGeneratedChatResult,
)
from src.application.use_cases.chat.continue_chat.continue_chat import (
    ContinueChatUseCase,
)
from src.application.use_cases.chat.continue_chat.continue_chat_dto import (
    ContinueChatInput,
)
from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.value_objects.chat.chat_turn_id import ChatTurnId
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt
from src.infrastructure.repositories.chat.in_memory_chat_repository import (
    InMemoryChatRepository,
)


USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class StubGenerationClient:
    def __init__(self) -> None:
        self.request: tuple[str, str] | None = None

    async def continue_chat(
        self, chat_id: str, prompt: str
    ) -> ContinueGeneratedChatResult:
        self.request = (chat_id, prompt)
        return ContinueGeneratedChatResult(chat_id=chat_id, answer="new answer")


async def _started_repository(answered_at: datetime) -> InMemoryChatRepository:
    repository = InMemoryChatRepository()
    chat = Chat.create(
        chat_id="session-1",
        title="existing title",
        user_id=USER_ID,
        answered_at=answered_at,
    )
    turn_id = ChatTurnId.generate()
    await repository.save_started_chat(
        chat,
        ChatMessage(
            "session-1",
            turn_id,
            MessageSender.USER,
            Prompt("first question"),
            answered_at,
        ),
        ChatMessage(
            "session-1",
            turn_id,
            MessageSender.LLM,
            "first answer",
            answered_at,
        ),
    )
    return repository


@pytest.mark.asyncio
async def test_continue_chat_saves_exchange_before_24_hours() -> None:
    last_updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user_sent_at = last_updated_at + timedelta(hours=24) - timedelta(microseconds=1)
    answered_at = user_sent_at + timedelta(seconds=1)
    repository = await _started_repository(last_updated_at)
    client = StubGenerationClient()
    times = iter((user_sent_at, answered_at))
    use_case = ContinueChatUseCase(
        client, repository, repository, now=lambda: next(times)
    )

    output = await use_case.execute(
        ContinueChatInput(user_id=USER_ID, chat_id="session-1", prompt="  next  ")
    )

    assert client.request == ("session-1", "next")
    assert output.chat_id == "session-1"
    assert output.answer == "new answer"
    assert output.title == "existing title"
    assert repository.chats["session-1"].last_updated_at == answered_at
    assert len(repository.messages) == 4
    assert repository.messages[-2].turn_id == repository.messages[-1].turn_id


@pytest.mark.asyncio
async def test_continue_chat_rejects_exactly_24_hours_without_side_effects() -> None:
    last_updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    repository = await _started_repository(last_updated_at)
    client = StubGenerationClient()
    use_case = ContinueChatUseCase(
        client,
        repository,
        repository,
        now=lambda: last_updated_at + timedelta(hours=24),
    )

    with pytest.raises(ChatContinuationExpiredError):
        await use_case.execute(
            ContinueChatInput(user_id=USER_ID, chat_id="session-1", prompt="next")
        )

    assert client.request is None
    assert repository.chats["session-1"].last_updated_at == last_updated_at
    assert len(repository.messages) == 2
