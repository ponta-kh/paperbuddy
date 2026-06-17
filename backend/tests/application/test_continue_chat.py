import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.exceptions import ChatContinuationExpiredError
from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
    ChatGenerationRateLimitError,
    ChatGenerationSessionUnavailableError,
    ChatGenerationUnavailableError,
    ContinueGeneratedChatResult,
    GeneratedChatCitation,
    GeneratedChatCitationSource,
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
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")
_CITATION_METADATA: dict[str, object] = {"page": 3}
CITATIONS = (
    GeneratedChatCitation(
        text="new answer",
        span_start=0,
        span_end=10,
        sources=(
            GeneratedChatCitationSource(
                content="source excerpt",
                location_type="S3",
                uri="s3://bucket/paper.pdf",
                metadata=_CITATION_METADATA,
            ),
        ),
    ),
)


def _chat(answered_at: datetime, user_id: UUID = USER_ID) -> Chat:
    return Chat.create(
        chat_id=CHAT_ID,
        session_id="session-1",
        title="existing title",
        user_id=user_id,
        answered_at=answered_at,
    )


@pytest.mark.asyncio
async def test_continue_chat_saves_exchange_at_24_hours_boundary() -> None:
    last_updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user_sent_at = last_updated_at + timedelta(hours=24)
    answered_at = user_sent_at + timedelta(seconds=1)
    chat = _chat(last_updated_at)
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat.return_value = chat
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    client.continue_chat.return_value = ContinueGeneratedChatResult(
        session_id="session-1", answer="new answer", citations=CITATIONS
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
    assert output.citations == CITATIONS
    assert output.title == "existing title"
    assert output.last_updated_at == answered_at
    saved_chat, user_message, llm_message = repository.save_exchange.await_args.args
    assert saved_chat is chat
    assert saved_chat.last_updated_at == answered_at
    assert user_message.request_id == llm_message.request_id == REQUEST_ID
    assert user_message.citations == ()
    assert llm_message.citations == CITATIONS


@pytest.mark.asyncio
async def test_continue_chat_rejects_after_24_hours_boundary_without_side_effects() -> (
    None
):
    last_updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chat = _chat(last_updated_at)
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat.return_value = chat
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    use_case = ContinueChatUseCase(
        client,
        repository,
        now=lambda: last_updated_at + timedelta(hours=24, seconds=1),
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
    repository.get_chat.return_value = chat
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    use_case = ContinueChatUseCase(
        client,
        repository,
        now=lambda: last_updated_at + timedelta(hours=24, seconds=1),
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
    assert getattr(record, "event") == "continue_chat_expired"
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert getattr(record, "chat_id") == str(CHAT_ID)
    assert "秘密の質問" not in caplog.text


@pytest.mark.asyncio
async def test_continue_chat_does_not_generate_when_chat_is_not_found() -> None:
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat.side_effect = ChatNotFoundError
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
async def test_continue_chat_does_not_generate_when_chat_owner_mismatches() -> None:
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat.return_value = _chat(
        datetime(2026, 1, 1, tzinfo=timezone.utc), user_id=OTHER_USER_ID
    )
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
    repository.get_chat.return_value = _chat(datetime(2026, 1, 1, tzinfo=timezone.utc))
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
async def test_continue_chat_treats_unavailable_session_as_expired(
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    chat = _chat(datetime(2026, 1, 1, tzinfo=timezone.utc))
    repository.get_chat.return_value = chat
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    client.continue_chat.side_effect = ChatGenerationSessionUnavailableError

    with (
        caplog.at_level(
            logging.WARNING,
            logger="src.application.use_cases.chat.continue_chat.continue_chat",
        ),
        pytest.raises(ChatContinuationExpiredError),
    ):
        await ContinueChatUseCase(
            client,
            repository,
            now=lambda: datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        ).execute(
            ContinueChatInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                prompt="秘密の質問",
                request_id=REQUEST_ID,
            )
        )

    record = caplog.records[0]
    assert getattr(record, "event") == "continue_chat_generation_session_unavailable"
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert getattr(record, "chat_id") == str(CHAT_ID)
    assert "秘密の質問" not in caplog.text
    repository.save_exchange.assert_not_awaited()
    assert chat.last_updated_at == datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_continue_chat_logs_rate_limit_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.get_chat.return_value = _chat(datetime(2026, 1, 1, tzinfo=timezone.utc))
    client = AsyncMock(spec=ChatGenerationClientProtocol)
    client.continue_chat.side_effect = ChatGenerationRateLimitError

    with (
        caplog.at_level(
            logging.WARNING,
            logger="src.application.use_cases.chat.continue_chat.continue_chat",
        ),
        pytest.raises(ChatGenerationRateLimitError),
    ):
        await ContinueChatUseCase(
            client,
            repository,
            now=lambda: datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        ).execute(
            ContinueChatInput(
                user_id=USER_ID,
                chat_id=CHAT_ID,
                prompt="秘密の質問",
                request_id=REQUEST_ID,
            )
        )

    record = caplog.records[0]
    assert getattr(record, "event") == "continue_chat_generation_rate_limited"
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert getattr(record, "chat_id") == str(CHAT_ID)
    assert "秘密の質問" not in caplog.text
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
    repository.get_chat.return_value = _chat(datetime(2026, 1, 1, tzinfo=timezone.utc))
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
