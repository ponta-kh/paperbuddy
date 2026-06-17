from dataclasses import dataclass
from typing import Protocol


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


@dataclass(frozen=True, slots=True)
class GeneratedChatCitationSource:
    content: str
    location_type: str | None
    uri: str | None
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class GeneratedChatCitation:
    text: str
    span_start: int | None
    span_end: int | None
    sources: tuple[GeneratedChatCitationSource, ...]


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
