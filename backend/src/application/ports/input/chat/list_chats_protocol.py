from typing import Protocol

from src.application.use_cases.chat.list_chats.list_chats_dto import (
    ListChatsInput,
    ListChatsOutput,
)


class ListChatsProtocol(Protocol):
    async def execute(self, query: ListChatsInput) -> ListChatsOutput: ...
