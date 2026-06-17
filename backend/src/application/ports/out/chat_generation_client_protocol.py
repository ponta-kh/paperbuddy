from dataclasses import dataclass
from typing import Protocol, TypeAlias

from src.domain.entities.chat.chat import ChatCitation, ChatCitationSource


class ChatGenerationError(Exception):
    pass


class ChatGenerationUnavailableError(ChatGenerationError):
    pass


class ChatGenerationRateLimitError(ChatGenerationUnavailableError):
    pass


class ChatGenerationPermissionDeniedError(ChatGenerationError):
    pass


class ChatGenerationConfigurationError(ChatGenerationError):
    pass


class ChatGenerationSessionUnavailableError(ChatGenerationError):
    pass


class InvalidChatGenerationResponseError(ChatGenerationError):
    pass


GeneratedChatCitationSource: TypeAlias = ChatCitationSource
GeneratedChatCitation: TypeAlias = ChatCitation


@dataclass(frozen=True, slots=True)
class StartGeneratedChatResult:
    session_id: str
    answer: str
    citations: tuple[GeneratedChatCitation, ...] = ()


@dataclass(frozen=True, slots=True)
class ContinueGeneratedChatResult:
    session_id: str
    answer: str
    citations: tuple[GeneratedChatCitation, ...] = ()


class ChatGenerationClientProtocol(Protocol):
    async def start_chat(self, prompt: str) -> StartGeneratedChatResult: ...

    async def continue_chat(
        self, session_id: str, prompt: str
    ) -> ContinueGeneratedChatResult: ...
