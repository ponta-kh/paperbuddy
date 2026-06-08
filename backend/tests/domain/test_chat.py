from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.exceptions.chat_exception import (
    InvalidChatIdError,
    InvalidChatTurnError,
    InvalidMessageSenderError,
    InvalidSessionIdError,
    MessageSentAtOutOfOrderError,
)
from src.domain.value_objects.chat.chat_turn_id import ChatTurnId
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt

CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000001")
ANSWERED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


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


def test_chat_message_rejects_non_uuid_chat_id() -> None:
    with pytest.raises(InvalidChatIdError):
        ChatMessage(  # type: ignore[arg-type]
            "chat-1",
            ChatTurnId.generate(),
            MessageSender.USER,
            Prompt("question"),
            ANSWERED_AT,
        )


def test_chat_message_rejects_naive_sent_at() -> None:
    with pytest.raises(ValueError, match="sent_at must be timezone-aware"):
        ChatMessage(
            CHAT_ID,
            ChatTurnId.generate(),
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
        ChatMessage(CHAT_ID, ChatTurnId.generate(), sender, content, ANSWERED_AT)


def _message_pair(
    chat_id: UUID,
    user_sent_at: datetime,
    llm_sent_at: datetime,
) -> tuple[ChatMessage, ChatMessage]:
    turn_id = ChatTurnId.generate()
    return (
        ChatMessage(
            chat_id, turn_id, MessageSender.USER, Prompt("question"), user_sent_at
        ),
        ChatMessage(chat_id, turn_id, MessageSender.LLM, "answer", llm_sent_at),
    )


def test_started_turn_requires_matching_turn_id() -> None:
    answered_at = ANSWERED_AT
    chat = _chat()
    user_message, llm_message = _message_pair(CHAT_ID, answered_at, answered_at)
    llm_message = ChatMessage(
        llm_message.chat_id,
        ChatTurnId.generate(),
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
