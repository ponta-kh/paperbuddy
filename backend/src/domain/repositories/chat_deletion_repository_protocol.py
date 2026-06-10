from typing import Protocol
from uuid import UUID


class ChatDeleteError(Exception):
    pass


class ChatDeletionRepositoryProtocol(Protocol):
    async def delete_chat(self, *, chat_id: UUID) -> None: ...
