from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RenameChatInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    chat_id: UUID
    title: str
    request_id: UUID


@dataclass(frozen=True, slots=True)
class RenameChatOutput:
    chat_id: UUID
    title: str
