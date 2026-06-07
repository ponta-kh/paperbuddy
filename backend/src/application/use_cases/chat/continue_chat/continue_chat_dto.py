from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class ContinueChatInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    chat_id: str
    prompt: str

    @field_validator("chat_id")
    @classmethod
    def validate_chat_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("chat_id must not be blank")
        return value


@dataclass(frozen=True, slots=True)
class ContinueChatOutput:
    chat_id: str
    answer: str
    title: str
