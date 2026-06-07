import asyncio
from dataclasses import replace
from uuid import UUID

from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.chat import ChatMessageRecord, ChatSummary
from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.repositories.chat_command_repository_protocol import (
    ChatConflictError,
    ChatNotFoundError,
    ChatSaveError,
)
from src.domain.value_objects.chat.prompt import Prompt


class InMemoryChatRepository:
    def __init__(self) -> None:
        self.chats: dict[str, Chat] = {}
        self.messages: list[ChatMessage] = []
        self._lock = asyncio.Lock()

    async def save_started_chat(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        async with self._lock:
            if chat.chat_id in self.chats:
                raise ChatSaveError
            self.chats[chat.chat_id] = replace(chat)
            self.messages.extend((user_message, llm_message))

    async def save_exchange(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        async with self._lock:
            persisted_chat = self.chats.get(chat.chat_id)
            if persisted_chat is None:
                raise ChatSaveError
            if persisted_chat.version != chat.version - 1:
                raise ChatConflictError
            self.chats[chat.chat_id] = replace(chat)
            self.messages.extend((user_message, llm_message))

    async def get_chat_for_continuation(self, *, chat_id: str, user_id: UUID) -> Chat:
        chat = self.chats.get(chat_id)
        if chat is None or chat.user_id != user_id:
            raise ChatNotFoundError
        return replace(chat)

    async def list_chats_by_user_id(self, user_id: UUID) -> tuple[ChatSummary, ...]:
        chats = sorted(
            (chat for chat in self.chats.values() if chat.user_id == user_id),
            key=lambda chat: chat.last_updated_at,
            reverse=True,
        )
        if not chats:
            raise RepositoryNotFoundError
        return tuple(
            ChatSummary(
                chat_id=chat.chat_id,
                title=chat.title,
                created_at=chat.created_at,
                last_updated_at=chat.last_updated_at,
            )
            for chat in chats
        )

    async def list_messages_by_chat_id(
        self,
        *,
        user_id: UUID,
        chat_id: str,
    ) -> tuple[ChatMessageRecord, ...]:
        chat = self.chats.get(chat_id)
        if chat is None or chat.user_id != user_id:
            raise RepositoryNotFoundError

        messages = sorted(
            (message for message in self.messages if message.chat_id == chat_id),
            key=lambda message: message.sent_at,
        )
        if not messages:
            raise RepositoryNotFoundError
        return tuple(
            ChatMessageRecord(
                turn_id=message.turn_id.value,
                sender=message.sender.value,
                content=(
                    message.content.value
                    if isinstance(message.content, Prompt)
                    else message.content
                ),
                sent_at=message.sent_at,
            )
            for message in messages
        )
