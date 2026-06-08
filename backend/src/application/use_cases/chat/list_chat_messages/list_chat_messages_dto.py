from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ListChatMessagesInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    chat_id: UUID


@dataclass(frozen=True, slots=True)
class ChatMessageOutput:
    turn_id: UUID
    sender: str
    content: str
    sent_at: datetime


@dataclass(frozen=True, slots=True)
class ListChatMessagesOutput:
    chat_id: UUID
    messages: tuple[ChatMessageOutput, ...]
