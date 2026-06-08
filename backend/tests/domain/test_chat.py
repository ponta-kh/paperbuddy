from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.exceptions.chat_exception import (
    InvalidChatIdError,
    InvalidChatTurnError,
    InvalidSessionIdError,
    MessageSentAtOutOfOrderError,
)
from src.domain.value_objects.chat.chat_turn_id import ChatTurnId
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt

CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")


def test_chat_rejects_non_uuid_chat_id() -> None:
    with pytest.raises(InvalidChatIdError):
        Chat.create(
            chat_id="chat-1",  # type: ignore[arg-type]
            session_id="session-1",
            title="title",
            user_id=UUID("00000000-0000-0000-0000-000000000001"),
            answered_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_chat_rejects_blank_session_id() -> None:
    with pytest.raises(InvalidSessionIdError):
        Chat.create(
            chat_id=CHAT_ID,
            session_id=" ",
            title="title",
            user_id=UUID("00000000-0000-0000-0000-000000000001"),
            answered_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


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
    answered_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chat = Chat.create(
        chat_id=CHAT_ID,
        session_id="session-1",
        title="title",
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        answered_at=answered_at,
    )
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
    answered_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chat = Chat.create(
        chat_id=CHAT_ID,
        session_id="session-1",
        title="title",
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        answered_at=answered_at,
    )
    user_message, llm_message = _message_pair(
        CHAT_ID,
        answered_at + timedelta(seconds=1),
        answered_at,
    )

    with pytest.raises(MessageSentAtOutOfOrderError):
        chat.validate_started_turn(user_message=user_message, llm_message=llm_message)


def test_record_exchange_updates_last_updated_at_and_version() -> None:
    answered_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    next_answered_at = answered_at + timedelta(seconds=2)
    chat = Chat.create(
        chat_id=CHAT_ID,
        session_id="session-1",
        title="title",
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        answered_at=answered_at,
    )
    user_message, llm_message = _message_pair(
        CHAT_ID, answered_at + timedelta(seconds=1), next_answered_at
    )

    chat.record_exchange(user_message=user_message, llm_message=llm_message)

    assert chat.last_updated_at == next_answered_at
    assert chat.version == 1
