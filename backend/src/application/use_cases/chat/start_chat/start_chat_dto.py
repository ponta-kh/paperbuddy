from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StartChatInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    prompt: str


@dataclass(frozen=True, slots=True)
class StartChatOutput:
    chat_id: str
    answer: str
    title: str
