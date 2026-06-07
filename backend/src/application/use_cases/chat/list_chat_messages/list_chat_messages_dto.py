from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class ListChatMessagesInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    chat_id: str

    @field_validator("chat_id")
    @classmethod
    def validate_chat_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("chat_id must not be blank")
        return value


@dataclass(frozen=True, slots=True)
class ChatMessageOutput:
    turn_id: UUID
    sender: str
    content: str
    sent_at: datetime


@dataclass(frozen=True, slots=True)
class ListChatMessagesOutput:
    chat_id: str
    messages: tuple[ChatMessageOutput, ...]
