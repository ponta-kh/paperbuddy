import asyncio
from dataclasses import replace

from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.repositories.chat_command_repository_protocol import ChatSaveError


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
            if chat.chat_id not in self.chats:
                raise ChatSaveError
            self.chats[chat.chat_id] = replace(chat)
            self.messages.extend((user_message, llm_message))
