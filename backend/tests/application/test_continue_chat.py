import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.exceptions import ChatContinuationExpiredError
from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
    ChatGenerationUnavailableError,
    ContinueGeneratedChatResult,
)
from src.application.use_cases.chat.continue_chat.continue_chat import (
    ContinueChatUseCase,
)
from src.application.use_cases.chat.continue_chat.continue_chat_dto import (
    ContinueChatInput,
)
from src.domain.entities.chat.chat import Chat
from src.domain.repositories.chat_command_repository_protocol import (
    ChatCommandRepositoryProtocol,
    ChatConflictError,
    ChatNotFoundError,
)

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")


def _chat(answered_at: datetime) -> Chat:
    return Chat.create(
        chat_id=CHAT_ID,
        session_id="session-1",
        title="existing title",
        user_id=USER_ID,
        answered_at=answered_at,
    )


@pytest.mark.asyncio
async def test_continue_chat_saves_exchange_before_24_hours() -> None:
    last_updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user_sent_at = last_updated_at + timedelta(hours=24) - timedelta(microseconds=1)
    answered_at = user_sent_at + timedelta(seconds=1)
    chat = _chat(last_updated_at)
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat_for_continuation.return_value = chat
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    client.continue_chat.return_value = ContinueGeneratedChatResult(
        session_id="session-1", answer="new answer"
    )
    times = iter((user_sent_at, answered_at))
    use_case = ContinueChatUseCase(client, repository, now=lambda: next(times))

    output = await use_case.execute(
        ContinueChatInput(
            user_id=USER_ID,
            chat_id=CHAT_ID,
            prompt="  next  ",
            request_id=REQUEST_ID,
        )
    )

    client.continue_chat.assert_awaited_once_with("session-1", "next")
    assert output.chat_id == CHAT_ID
    assert output.answer == "new answer"
    assert output.title == "existing title"
    assert output.last_updated_at == answered_at
    saved_chat, user_message, llm_message = repository.save_exchange.await_args.args
    assert saved_chat is chat
    assert saved_chat.last_updated_at == answered_at
    assert user_message.request_id == llm_message.request_id == REQUEST_ID


@pytest.mark.asyncio
async def test_continue_chat_rejects_exactly_24_hours_without_side_effects() -> None:
    last_updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chat = _chat(last_updated_at)
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat_for_continuation.return_value = chat
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    use_case = ContinueChatUseCase(
        client,
        repository,
        now=lambda: last_updated_at + timedelta(hours=24),
    )

    with pytest.raises(ChatContinuationExpiredError):
        await use_case.execute(
            ContinueChatInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                prompt="next",
                request_id=REQUEST_ID,
            )
        )

    client.continue_chat.assert_not_awaited()
    repository.save_exchange.assert_not_awaited()
    assert chat.last_updated_at == last_updated_at


@pytest.mark.asyncio
async def test_continue_chat_logs_expired_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    last_updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chat = _chat(last_updated_at)
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat_for_continuation.return_value = chat
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    use_case = ContinueChatUseCase(
        client,
        repository,
        now=lambda: last_updated_at + timedelta(hours=24),
    )

    with (
        caplog.at_level(
            logging.WARNING,
            logger="src.application.use_cases.chat.continue_chat.continue_chat",
        ),
        pytest.raises(ChatContinuationExpiredError),
    ):
        await use_case.execute(
            ContinueChatInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                prompt="秘密の質問",
                request_id=REQUEST_ID,
            )
        )

    record = caplog.records[0]
    assert record.event == "continue_chat_expired"
    assert record.request_id == str(REQUEST_ID)
    assert record.user_id == str(USER_ID)
    assert record.chat_id == str(CHAT_ID)
    assert "秘密の質問" not in caplog.text


@pytest.mark.asyncio
async def test_continue_chat_does_not_generate_when_chat_is_not_found() -> None:
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat_for_continuation.side_effect = ChatNotFoundError
    client = AsyncMock(spec=ChatGenerationClientProtocol)

    with pytest.raises(ChatNotFoundError):
        await ContinueChatUseCase(client, repository).execute(
            ContinueChatInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                prompt="next",
                request_id=REQUEST_ID,
            )
        )

    client.continue_chat.assert_not_awaited()
    repository.save_exchange.assert_not_awaited()


@pytest.mark.asyncio
async def test_continue_chat_does_not_save_when_generation_fails() -> None:
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat_for_continuation.return_value = _chat(
        datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    client.continue_chat.side_effect = ChatGenerationUnavailableError

    with pytest.raises(ChatGenerationUnavailableError):
        await ContinueChatUseCase(
            client,
            repository,
            now=lambda: datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        ).execute(
            ContinueChatInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                prompt="next",
                request_id=REQUEST_ID,
            )
        )

    repository.save_exchange.assert_not_awaited()


@pytest.mark.asyncio
async def test_continue_chat_propagates_repository_conflict() -> None:
    times = iter(
        (
            datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 1, 1, tzinfo=timezone.utc),
        )
    )
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat_for_continuation.return_value = _chat(
        datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    repository.save_exchange.side_effect = ChatConflictError
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    client.continue_chat.return_value = ContinueGeneratedChatResult(
        session_id="session-1", answer="new answer"
    )

    with pytest.raises(ChatConflictError):
        await ContinueChatUseCase(client, repository, now=lambda: next(times)).execute(
            ContinueChatInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                prompt="next",
                request_id=REQUEST_ID,
            )
        )
