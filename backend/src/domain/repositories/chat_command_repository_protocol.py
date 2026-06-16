from typing import Protocol
from uuid import UUID

from src.domain.entities.chat.chat import Chat, ChatMessage


class ChatSaveError(Exception):
    pass


class ChatLoadError(Exception):
    pass


class ChatConflictError(Exception):
    pass


class ChatNotFoundError(Exception):
    pass


class ChatCommandRepositoryProtocol(Protocol):
    async def get_chat(
        self,
        *,
        chat_id: UUID,
    ) -> Chat: ...

    async def save_started_chat(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None: ...

    async def save_exchange(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None: ...
