from typing import Protocol

from src.application.use_cases.chat.delete_chat.delete_chat_dto import DeleteChatInput


class DeleteChatProtocol(Protocol):
    async def execute(self, command: DeleteChatInput) -> None: ...
