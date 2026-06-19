from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import UUID

import pytest

from src.domain.entities.chat.chat import (
    Chat,
    ChatCitation,
    ChatCitationSource,
    ChatMessage,
)
from src.domain.exceptions.chat_exception import (
    ChatContinuationExpiredError,
    ChatOwnershipMismatchError,
    InvalidChatCitationError,
    InvalidChatIdError,
    InvalidChatTurnError,
    InvalidMessageSenderError,
    InvalidSessionIdError,
    MessageSentAtOutOfOrderError,
)
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt

CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")
ANSWERED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
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


def _chat(answered_at: datetime = ANSWERED_AT) -> Chat:
    return Chat.create(
        chat_id=CHAT_ID,
        session_id="session-1",
        title="title",
        user_id=USER_ID,
        answered_at=answered_at,
    )


def test_chat_rejects_non_uuid_chat_id() -> None:
    with pytest.raises(InvalidChatIdError):
        Chat.create(
            chat_id="chat-1",  # type: ignore[arg-type]
            session_id="session-1",
            title="title",
            user_id=USER_ID,
            answered_at=ANSWERED_AT,
        )


def test_chat_rejects_blank_session_id() -> None:
    with pytest.raises(InvalidSessionIdError):
        Chat.create(
            chat_id=CHAT_ID,
            session_id=" ",
            title="title",
            user_id=USER_ID,
            answered_at=ANSWERED_AT,
        )


def test_chat_rejects_naive_answered_at() -> None:
    with pytest.raises(ValueError, match="answered_at must be timezone-aware"):
        Chat.create(
            chat_id=CHAT_ID,
            session_id="session-1",
            title="title",
            user_id=USER_ID,
            answered_at=datetime(2026, 1, 1),
        )


def test_chat_create_sets_initial_state() -> None:
    chat = _chat()

    assert chat.created_at == ANSWERED_AT
    assert chat.last_updated_at == ANSWERED_AT
    assert chat.version == 0


def test_chat_accepts_owner() -> None:
    chat = _chat()

    chat.ensure_owned_by(USER_ID)


def test_chat_rejects_owner_mismatch() -> None:
    chat = _chat()

    with pytest.raises(ChatOwnershipMismatchError):
        chat.ensure_owned_by(OTHER_USER_ID)


def test_chat_message_rejects_non_uuid_chat_id() -> None:
    with pytest.raises(InvalidChatIdError):
        ChatMessage(
            cast(UUID, "chat-1"),
            REQUEST_ID,
            MessageSender.USER,
            Prompt("question"),
            ANSWERED_AT,
        )


def test_chat_message_rejects_invalid_request_id() -> None:
    with pytest.raises(InvalidChatTurnError):
        ChatMessage(
            CHAT_ID,
            cast(UUID, "request-1"),
            MessageSender.USER,
            Prompt("question"),
            ANSWERED_AT,
        )


def test_chat_message_rejects_naive_sent_at() -> None:
    with pytest.raises(ValueError, match="sent_at must be timezone-aware"):
        ChatMessage(
            CHAT_ID,
            REQUEST_ID,
            MessageSender.USER,
            Prompt("question"),
            datetime(2026, 1, 1),
        )


@pytest.mark.parametrize(
    ("sender", "content"),
    [
        (MessageSender.USER, "question"),
        (MessageSender.LLM, Prompt("answer")),
    ],
)
def test_chat_message_rejects_content_for_wrong_sender(
    sender: MessageSender,
    content: Prompt | str,
) -> None:
    with pytest.raises(InvalidMessageSenderError):
        ChatMessage(
            CHAT_ID,
            REQUEST_ID,
            sender,
            content,
            ANSWERED_AT,
        )


def test_chat_message_rejects_citations_for_user_message() -> None:
    with pytest.raises(InvalidChatCitationError):
        ChatMessage(
            CHAT_ID,
            REQUEST_ID,
            MessageSender.USER,
            Prompt("question"),
            ANSWERED_AT,
            citations=CITATIONS,
        )


def test_chat_message_accepts_citations_for_llm_message() -> None:
    message = ChatMessage(
        CHAT_ID,
        REQUEST_ID,
        MessageSender.LLM,
        "answer",
        ANSWERED_AT,
        citations=CITATIONS,
    )

    assert message.citations == CITATIONS


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("content", 1),
        ("location_type", 1),
        ("uri", 1),
        ("metadata", (("page", 1),)),
    ],
)
def test_chat_citation_source_rejects_invalid_field(
    field_name: str,
    invalid_value: object,
) -> None:
    values: dict[str, object] = {
        "content": "source excerpt",
        "location_type": "S3",
        "uri": "s3://bucket/paper.pdf",
        "metadata": _CITATION_METADATA,
    }
    values[field_name] = invalid_value

    with pytest.raises(InvalidChatCitationError):
        ChatCitationSource(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("text", 1),
        ("span_start", "0"),
        ("span_end", "6"),
        ("sources", [CITATIONS[0].sources[0]]),
    ],
)
def test_chat_citation_rejects_invalid_field(
    field_name: str,
    invalid_value: object,
) -> None:
    values: dict[str, object] = {
        "text": "answer",
        "span_start": 0,
        "span_end": 6,
        "sources": CITATIONS[0].sources,
    }
    values[field_name] = invalid_value

    with pytest.raises(InvalidChatCitationError):
        ChatCitation(**values)  # type: ignore[arg-type]


def test_chat_message_rejects_invalid_citations_container() -> None:
    with pytest.raises(InvalidChatCitationError):
        ChatMessage(
            CHAT_ID,
            REQUEST_ID,
            MessageSender.LLM,
            "answer",
            ANSWERED_AT,
            citations=[CITATIONS[0]],  # type: ignore[arg-type]
        )


def _message_pair(
    chat_id: UUID,
    user_sent_at: datetime,
    llm_sent_at: datetime,
) -> tuple[ChatMessage, ChatMessage]:
    return (
        ChatMessage(
            chat_id,
            REQUEST_ID,
            MessageSender.USER,
            Prompt("question"),
            user_sent_at,
        ),
        ChatMessage(
            chat_id,
            REQUEST_ID,
            MessageSender.LLM,
            "answer",
            llm_sent_at,
        ),
    )


def test_started_turn_requires_matching_request_id() -> None:
    answered_at = ANSWERED_AT
    chat = _chat()
    user_message, llm_message = _message_pair(CHAT_ID, answered_at, answered_at)
    llm_message = ChatMessage(
        llm_message.chat_id,
        UUID("019ecde4-0000-7000-8000-000000000002"),
        llm_message.sender,
        llm_message.content,
        llm_message.sent_at,
    )

    with pytest.raises(InvalidChatTurnError):
        chat.validate_started_turn(user_message=user_message, llm_message=llm_message)


def test_started_turn_rejects_user_message_after_llm_answer() -> None:
    answered_at = ANSWERED_AT
    chat = _chat()
    user_message, llm_message = _message_pair(
        CHAT_ID,
        answered_at + timedelta(seconds=1),
        answered_at,
    )

    with pytest.raises(MessageSentAtOutOfOrderError):
        chat.validate_started_turn(user_message=user_message, llm_message=llm_message)


def test_started_turn_rejects_llm_message_not_matching_chat_creation() -> None:
    chat = _chat()
    user_message, llm_message = _message_pair(
        CHAT_ID,
        ANSWERED_AT,
        ANSWERED_AT + timedelta(microseconds=1),
    )

    with pytest.raises(MessageSentAtOutOfOrderError):
        chat.validate_started_turn(user_message=user_message, llm_message=llm_message)


def test_started_turn_accepts_matching_messages() -> None:
    chat = _chat()
    user_message, llm_message = _message_pair(CHAT_ID, ANSWERED_AT, ANSWERED_AT)

    chat.validate_started_turn(user_message=user_message, llm_message=llm_message)


def test_record_exchange_updates_last_updated_at_and_version() -> None:
    answered_at = ANSWERED_AT
    next_answered_at = answered_at + timedelta(seconds=2)
    chat = _chat()
    user_message, llm_message = _message_pair(
        CHAT_ID, answered_at + timedelta(seconds=1), next_answered_at
    )

    chat.record_exchange(user_message=user_message, llm_message=llm_message)

    assert chat.last_updated_at == next_answered_at
    assert chat.version == 1


def test_chat_allows_continuation_at_24_hours_boundary() -> None:
    chat = _chat()

    chat.ensure_continuable_at(ANSWERED_AT + timedelta(hours=24))


def test_chat_rejects_continuation_after_24_hours_boundary() -> None:
    chat = _chat()

    with pytest.raises(ChatContinuationExpiredError):
        chat.ensure_continuable_at(ANSWERED_AT + timedelta(hours=24, seconds=1))


def test_chat_rejects_naive_continuation_time() -> None:
    chat = _chat()

    with pytest.raises(ValueError, match="requested_at must be timezone-aware"):
        chat.ensure_continuable_at(datetime(2026, 1, 2))


def test_record_exchange_rejects_user_message_before_last_update() -> None:
    chat = _chat()
    user_message, llm_message = _message_pair(
        CHAT_ID,
        ANSWERED_AT - timedelta(microseconds=1),
        ANSWERED_AT,
    )

    with pytest.raises(MessageSentAtOutOfOrderError):
        chat.record_exchange(user_message=user_message, llm_message=llm_message)


def test_record_exchange_rejects_llm_message_before_user_message() -> None:
    chat = _chat()
    user_message, llm_message = _message_pair(
        CHAT_ID,
        ANSWERED_AT + timedelta(seconds=1),
        ANSWERED_AT,
    )

    with pytest.raises(MessageSentAtOutOfOrderError):
        chat.record_exchange(user_message=user_message, llm_message=llm_message)
