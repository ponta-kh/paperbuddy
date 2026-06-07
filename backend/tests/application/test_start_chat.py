from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.application.ports.out.chat_generation_client_protocol import (
    StartGeneratedChatResult,
)
from src.application.use_cases.chat.start_chat.start_chat import StartChatUseCase
from src.application.use_cases.chat.start_chat.start_chat_dto import StartChatInput
from src.domain.value_objects.chat.message_sender import MessageSender
from src.infrastructure.repositories.chat.in_memory_chat_repository import (
    InMemoryChatRepository,
)


class StubGenerationClient:
    def __init__(self) -> None:
        self.prompt: str | None = None

    async def start_chat(self, prompt: str) -> StartGeneratedChatResult:
        self.prompt = prompt
        return StartGeneratedChatResult(
            chat_id="session-1", answer="answer", title="title"
        )


@pytest.mark.asyncio
async def test_start_chat_saves_chat_and_turn() -> None:
    generation_client = StubGenerationClient()
    repository = InMemoryChatRepository()
    times = iter(
        [
            datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
        ]
    )
    use_case = StartChatUseCase(generation_client, repository, now=lambda: next(times))

    output = await use_case.execute(
        StartChatInput(
            user_id=UUID("00000000-0000-0000-0000-000000000001"), prompt="  question  "
        )
    )

    assert generation_client.prompt == "question"
    assert output.chat_id == "session-1"
    assert (
        repository.chats["session-1"].created_at
        == repository.chats["session-1"].last_updated_at
    )
    assert len(repository.messages) == 2
    assert repository.messages[0].turn_id == repository.messages[1].turn_id
    assert repository.messages[0].sender is MessageSender.USER
    assert repository.messages[1].sender is MessageSender.LLM
