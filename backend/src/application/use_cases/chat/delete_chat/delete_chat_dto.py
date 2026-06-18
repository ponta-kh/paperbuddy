from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DeleteChatInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    chat_id: UUID
    user_id: UUID
    request_id: UUID
