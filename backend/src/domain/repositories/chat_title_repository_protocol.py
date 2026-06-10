from typing import Protocol
from uuid import UUID


class ChatTitleUpdateError(Exception):
    pass


class ChatTitleRepositoryProtocol(Protocol):
    async def update_title(
        self,
        *,
        chat_id: UUID,
        user_id: UUID,
        title: str,
    ) -> None: ...
