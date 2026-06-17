from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.domain.entities.chat.chat import ChatCitation


@dataclass(frozen=True, slots=True)
class ChatSummary:
    chat_id: UUID
    title: str
    created_at: datetime
    last_updated_at: datetime


@dataclass(frozen=True, slots=True)
class ChatMessageRecord:
    request_id: UUID
    sender: str
    content: str
    sent_at: datetime
    citations: tuple[ChatCitation, ...] = ()


class ChatQueryRepositoryProtocol(Protocol):
    async def list_chats_by_user_id(self, user_id: UUID) -> tuple[ChatSummary, ...]: ...

    async def list_messages_by_chat_id(
        self,
        *,
        user_id: UUID,
        chat_id: UUID,
    ) -> tuple[ChatMessageRecord, ...]: ...
