from typing import Protocol

from src.domain.entities.chat.chat import Chat, ChatMessage


class ChatSaveError(Exception):
    pass


class ChatCommandRepositoryProtocol(Protocol):
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
