from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.application.ports.out.chat_generation_client_protocol import (
    GeneratedChatCitation,
)


class StartChatInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    user_id: UUID
    prompt: str
    request_id: UUID


@dataclass(frozen=True, slots=True)
class StartChatOutput:
    chat_id: UUID
    answer: str
    citations: tuple[GeneratedChatCitation, ...]
    title: str
    last_updated_at: datetime
