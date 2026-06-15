from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContinueChatInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    chat_id: UUID
    prompt: str


@dataclass(frozen=True, slots=True)
class ContinueChatOutput:
    chat_id: UUID
    answer: str
    title: str
    last_updated_at: datetime
