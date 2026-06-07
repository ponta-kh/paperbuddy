from typing import Protocol

from src.application.use_cases.chat.start_chat.start_chat_dto import (
    StartChatInput,
    StartChatOutput,
)


class StartChatProtocol(Protocol):
    async def execute(self, command: StartChatInput) -> StartChatOutput: ...
