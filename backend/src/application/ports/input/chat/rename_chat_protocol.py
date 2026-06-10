from typing import Protocol

from src.application.use_cases.chat.rename_chat.rename_chat_dto import (
    RenameChatInput,
    RenameChatOutput,
)


class RenameChatProtocol(Protocol):
    async def execute(self, command: RenameChatInput) -> RenameChatOutput: ...
