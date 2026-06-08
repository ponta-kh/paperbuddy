from dataclasses import replace
from uuid import UUID

from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.repositories.chat_command_repository_protocol import ChatNotFoundError


class RecordingChatRepository:
    def __init__(self) -> None:
        self.chats: dict[UUID, Chat] = {}
        self.messages: list[ChatMessage] = []

    async def save_started_chat(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        self.chats[chat.chat_id] = replace(chat)
        self.messages.extend((user_message, llm_message))

    async def get_chat_for_continuation(self, *, chat_id: UUID, user_id: UUID) -> Chat:
        chat = self.chats.get(chat_id)
        if chat is None or chat.user_id != user_id:
            raise ChatNotFoundError
        return replace(chat)

    async def save_exchange(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        self.chats[chat.chat_id] = replace(chat)
        self.messages.extend((user_message, llm_message))
