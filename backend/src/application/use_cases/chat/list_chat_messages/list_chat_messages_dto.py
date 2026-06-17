from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domain.entities.chat.chat import ChatCitation


class ListChatMessagesInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    chat_id: UUID
    request_id: UUID


@dataclass(frozen=True, slots=True)
class ChatMessageOutput:
    request_id: UUID
    sender: str
    content: str
    sent_at: datetime
    citations: tuple[ChatCitation, ...] = ()


@dataclass(frozen=True, slots=True)
class ListChatMessagesOutput:
    chat_id: UUID
    messages: tuple[ChatMessageOutput, ...]
