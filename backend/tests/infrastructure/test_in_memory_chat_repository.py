from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.application.exceptions import RepositoryNotFoundError
from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.value_objects.chat.chat_turn_id import ChatTurnId
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt
from src.infrastructure.repositories.chat.in_memory_chat_repository import (
    InMemoryChatRepository,
)


USER_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def _chat(chat_id: str, user_id: UUID, answered_at: datetime) -> Chat:
    return Chat.create(
        chat_id=chat_id,
        title=f"title-{chat_id}",
        user_id=user_id,
        answered_at=answered_at,
    )


def _messages(
    chat_id: str, user_sent_at: datetime, llm_sent_at: datetime
) -> tuple[ChatMessage, ChatMessage]:
    turn_id = ChatTurnId.generate()
    return (
        ChatMessage(
            chat_id, turn_id, MessageSender.USER, Prompt("question"), user_sent_at
        ),
        ChatMessage(chat_id, turn_id, MessageSender.LLM, "answer", llm_sent_at),
    )


@pytest.mark.asyncio
async def test_list_chats_filters_user_and_sorts_by_last_updated_descending() -> None:
    repository = InMemoryChatRepository()
    older = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer = older + timedelta(days=1)
    for chat in (
        _chat("older", USER_ID, older),
        _chat("other", OTHER_USER_ID, newer),
        _chat("newer", USER_ID, newer),
    ):
        user_message, llm_message = _messages(
            chat.chat_id, chat.created_at, chat.created_at
        )
        await repository.save_started_chat(chat, user_message, llm_message)

    chats = await repository.list_chats_by_user_id(USER_ID)

    assert [chat.chat_id for chat in chats] == ["newer", "older"]


@pytest.mark.asyncio
async def test_list_chats_raises_not_found_when_user_has_no_chats() -> None:
    repository = InMemoryChatRepository()

    with pytest.raises(RepositoryNotFoundError):
        await repository.list_chats_by_user_id(USER_ID)


@pytest.mark.asyncio
async def test_list_messages_sorts_by_sent_at_and_converts_content() -> None:
    repository = InMemoryChatRepository()
    user_sent_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    llm_sent_at = user_sent_at + timedelta(seconds=1)
    chat = _chat("chat-1", USER_ID, llm_sent_at)
    user_message, llm_message = _messages("chat-1", user_sent_at, llm_sent_at)
    await repository.save_started_chat(chat, user_message, llm_message)

    messages = await repository.list_messages_by_chat_id(
        user_id=USER_ID, chat_id="chat-1"
    )

    assert [message.sender for message in messages] == ["user", "llm"]
    assert [message.content for message in messages] == ["question", "answer"]


@pytest.mark.asyncio
async def test_list_messages_hides_other_users_chat() -> None:
    repository = InMemoryChatRepository()
    answered_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chat = _chat("chat-1", OTHER_USER_ID, answered_at)
    user_message, llm_message = _messages("chat-1", answered_at, answered_at)
    await repository.save_started_chat(chat, user_message, llm_message)

    with pytest.raises(RepositoryNotFoundError):
        await repository.list_messages_by_chat_id(user_id=USER_ID, chat_id="chat-1")


@pytest.mark.asyncio
async def test_get_chat_by_id_for_user_returns_detached_copy() -> None:
    repository = InMemoryChatRepository()
    answered_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chat = _chat("chat-1", USER_ID, answered_at)
    user_message, llm_message = _messages("chat-1", answered_at, answered_at)
    await repository.save_started_chat(chat, user_message, llm_message)

    loaded = await repository.get_chat_by_id_for_user(chat_id="chat-1", user_id=USER_ID)
    loaded.last_updated_at = answered_at + timedelta(hours=1)

    assert repository.chats["chat-1"].last_updated_at == answered_at


@pytest.mark.asyncio
async def test_get_chat_by_id_for_user_hides_other_users_chat() -> None:
    repository = InMemoryChatRepository()
    answered_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chat = _chat("chat-1", OTHER_USER_ID, answered_at)
    user_message, llm_message = _messages("chat-1", answered_at, answered_at)
    await repository.save_started_chat(chat, user_message, llm_message)

    with pytest.raises(RepositoryNotFoundError):
        await repository.get_chat_by_id_for_user(chat_id="chat-1", user_id=USER_ID)
