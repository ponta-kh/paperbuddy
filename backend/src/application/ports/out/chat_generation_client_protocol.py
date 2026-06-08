from dataclasses import dataclass
from typing import Protocol


class ChatGenerationUnavailableError(Exception):
    pass


class InvalidChatGenerationResponseError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class StartGeneratedChatResult:
    session_id: str
    answer: str
    title: str


@dataclass(frozen=True, slots=True)
class ContinueGeneratedChatResult:
    session_id: str
    answer: str


class ChatGenerationClientProtocol(Protocol):
    async def start_chat(self, prompt: str) -> StartGeneratedChatResult: ...

    async def continue_chat(
        self, session_id: str, prompt: str
    ) -> ContinueGeneratedChatResult: ...
