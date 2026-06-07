from typing import Protocol

from src.application.use_cases.chat.continue_chat.continue_chat_dto import (
    ContinueChatInput,
    ContinueChatOutput,
)


class ContinueChatProtocol(Protocol):
    async def execute(self, command: ContinueChatInput) -> ContinueChatOutput: ...
