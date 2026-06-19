import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
    ChatGenerationConfigurationError,
    ChatGenerationPermissionDeniedError,
    ChatGenerationRateLimitError,
    ChatGenerationUnavailableError,
    GeneratedChatCitation,
    GeneratedChatCitationSource,
    InvalidChatGenerationResponseError,
    StartGeneratedChatResult,
)
from src.application.use_cases.chat.start_chat.start_chat import StartChatUseCase
from src.application.use_cases.chat.start_chat.start_chat_dto import StartChatInput
from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.repositories.chat_command_repository_protocol import (
    ChatCommandRepositoryProtocol,
    ChatSaveError,
)
from src.domain.value_objects.chat.message_sender import MessageSender

CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000001")
REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")
USER_SENT_AT = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
ANSWERED_AT = datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc)
_CITATION_METADATA: dict[str, object] = {"page": 3}
CITATIONS = (
    GeneratedChatCitation(
        text="answer",
        span_start=0,
        span_end=6,
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


def _use_case(
    generation_client: AsyncMock,
    repository: AsyncMock,
) -> StartChatUseCase:
    times = iter((USER_SENT_AT, ANSWERED_AT))
    return StartChatUseCase(
        generation_client,
        repository,
        now=lambda: next(times),
        generate_chat_id=lambda: CHAT_ID,
    )


@pytest.mark.asyncio
async def test_start_chat_generates_uuid7_chat_id_by_default() -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.return_value = StartGeneratedChatResult(
        session_id="session-1", answer="answer"
    )
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    times = iter((USER_SENT_AT, ANSWERED_AT))
    use_case = StartChatUseCase(
        generation_client,
        repository,
        now=lambda: next(times),
    )

    output = await use_case.execute(
        StartChatInput(user_id=USER_ID, prompt="question", request_id=REQUEST_ID)
    )

    assert output.chat_id.version == 7


@pytest.mark.asyncio
async def test_start_chat_saves_chat_and_turn() -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.return_value = StartGeneratedChatResult(
        session_id="session-1", answer="answer", citations=CITATIONS
    )
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)

    output = await _use_case(generation_client, repository).execute(
        StartChatInput(user_id=USER_ID, prompt="  question  ", request_id=REQUEST_ID)
    )

    generation_client.start_chat.assert_awaited_once_with("question")
    assert output.chat_id == CHAT_ID
    assert output.citations == CITATIONS
    assert output.last_updated_at == ANSWERED_AT
    saved_chat, user_message, llm_message = repository.save_started_chat.await_args.args
    assert isinstance(saved_chat, Chat)
    assert isinstance(user_message, ChatMessage)
    assert isinstance(llm_message, ChatMessage)
    assert saved_chat.session_id == "session-1"
    assert saved_chat.title == "question"
    assert saved_chat.created_at == saved_chat.last_updated_at == ANSWERED_AT
    assert user_message.request_id == llm_message.request_id == REQUEST_ID
    assert user_message.sender is MessageSender.USER
    assert llm_message.sender is MessageSender.LLM
    assert user_message.citations == ()
    assert llm_message.citations == CITATIONS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prompt", "expected_title"),
    [
        ("1234567890", "1234567890"),
        ("1234567890a", "1234567890..."),
        ("  1234567890a  ", "1234567890..."),
    ],
)
async def test_start_chat_generates_title_from_prompt(
    prompt: str,
    expected_title: str,
) -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.return_value = StartGeneratedChatResult(
        session_id="session-1", answer="answer"
    )
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)

    output = await _use_case(generation_client, repository).execute(
        StartChatInput(user_id=USER_ID, prompt=prompt, request_id=REQUEST_ID)
    )

    saved_chat = repository.save_started_chat.await_args.args[0]
    assert output.title == expected_title
    assert saved_chat.title == expected_title


@pytest.mark.asyncio
async def test_start_chat_does_not_save_when_generation_fails() -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.side_effect = ChatGenerationUnavailableError
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)

    with pytest.raises(ChatGenerationUnavailableError):
        await _use_case(generation_client, repository).execute(
            StartChatInput(user_id=USER_ID, prompt="question", request_id=REQUEST_ID)
        )

    repository.save_started_chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_start_chat_logs_generation_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.side_effect = ChatGenerationUnavailableError
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)

    with (
        caplog.at_level(
            logging.ERROR,
            logger="src.application.use_cases.chat.start_chat.start_chat",
        ),
        pytest.raises(ChatGenerationUnavailableError),
    ):
        await _use_case(generation_client, repository).execute(
            StartChatInput(user_id=USER_ID, prompt="秘密の質問", request_id=REQUEST_ID)
        )

    record = caplog.records[0]
    assert getattr(record, "event") == "start_chat_generation_unavailable"
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert "秘密の質問" not in caplog.text


@pytest.mark.asyncio
async def test_start_chat_logs_rate_limit_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.side_effect = ChatGenerationRateLimitError
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)

    with (
        caplog.at_level(
            logging.WARNING,
            logger="src.application.use_cases.chat.start_chat.start_chat",
        ),
        pytest.raises(ChatGenerationRateLimitError),
    ):
        await _use_case(generation_client, repository).execute(
            StartChatInput(user_id=USER_ID, prompt="秘密の質問", request_id=REQUEST_ID)
        )

    record = caplog.records[0]
    assert getattr(record, "event") == "start_chat_generation_rate_limited"
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert "秘密の質問" not in caplog.text
    repository.save_started_chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_start_chat_logs_configuration_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.side_effect = ChatGenerationConfigurationError
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)

    with (
        caplog.at_level(
            logging.ERROR,
            logger="src.application.use_cases.chat.start_chat.start_chat",
        ),
        pytest.raises(ChatGenerationConfigurationError),
    ):
        await _use_case(generation_client, repository).execute(
            StartChatInput(user_id=USER_ID, prompt="秘密の質問", request_id=REQUEST_ID)
        )

    record = caplog.records[0]
    assert getattr(record, "event") == "start_chat_generation_configuration_error"
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert "秘密の質問" not in caplog.text
    repository.save_started_chat.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("generation_error", "expected_event", "expected_level"),
    [
        (
            ChatGenerationPermissionDeniedError,
            "start_chat_generation_permission_denied",
            logging.ERROR,
        ),
        (
            InvalidChatGenerationResponseError,
            "start_chat_generation_invalid_response",
            logging.WARNING,
        ),
    ],
)
async def test_start_chat_logs_generation_error_variants(
    generation_error: type[Exception],
    expected_event: str,
    expected_level: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.side_effect = generation_error
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)

    with (
        caplog.at_level(
            expected_level,
            logger="src.application.use_cases.chat.start_chat.start_chat",
        ),
        pytest.raises(generation_error),
    ):
        await _use_case(generation_client, repository).execute(
            StartChatInput(user_id=USER_ID, prompt="秘密の質問", request_id=REQUEST_ID)
        )

    record = caplog.records[0]
    assert getattr(record, "event") == expected_event
    assert getattr(record, "request_id") == str(REQUEST_ID)
    assert getattr(record, "user_id") == str(USER_ID)
    assert "秘密の質問" not in caplog.text
    repository.save_started_chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_start_chat_propagates_repository_save_error() -> None:
    generation_client = AsyncMock(spec=ChatGenerationClientProtocol)
    generation_client.start_chat.return_value = StartGeneratedChatResult(
        session_id="session-1", answer="answer"
    )
    repository = AsyncMock(spec=ChatCommandRepositoryProtocol)
    repository.save_started_chat.side_effect = ChatSaveError

    with pytest.raises(ChatSaveError):
        await _use_case(generation_client, repository).execute(
            StartChatInput(user_id=USER_ID, prompt="question", request_id=REQUEST_ID)
        )
