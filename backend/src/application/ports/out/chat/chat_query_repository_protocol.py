from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ChatSummary:
    chat_id: str
    title: str
    created_at: datetime
    last_updated_at: datetime


@dataclass(frozen=True, slots=True)
class ChatMessageRecord:
    turn_id: UUID
    sender: str
    content: str
    sent_at: datetime


class ChatQueryRepositoryProtocol(Protocol):
    async def list_chats_by_user_id(self, user_id: UUID) -> tuple[ChatSummary, ...]: ...

    async def list_messages_by_chat_id(
        self,
        *,
        user_id: UUID,
        chat_id: str,
    ) -> tuple[ChatMessageRecord, ...]: ...
