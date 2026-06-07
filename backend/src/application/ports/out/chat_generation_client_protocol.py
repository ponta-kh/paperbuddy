from dataclasses import dataclass
from typing import Protocol


class ChatGenerationUnavailableError(Exception):
    pass


class InvalidChatGenerationResponseError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class StartGeneratedChatResult:
    chat_id: str
    answer: str
    title: str


class ChatGenerationClientProtocol(Protocol):
    async def start_chat(self, prompt: str) -> StartGeneratedChatResult: ...
