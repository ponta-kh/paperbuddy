from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ListChatsInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    request_id: UUID


@dataclass(frozen=True, slots=True)
class ChatSummaryOutput:
    chat_id: UUID
    title: str
    created_at: datetime
    last_updated_at: datetime


@dataclass(frozen=True, slots=True)
class ListChatsOutput:
    chats: tuple[ChatSummaryOutput, ...]
