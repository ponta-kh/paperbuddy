from dataclasses import dataclass

from src.domain.exceptions.chat_exception import InvalidPromptError, PromptTooLongError

MAX_PROMPT_LENGTH = 1000


@dataclass(frozen=True, slots=True)
class Prompt:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidPromptError
        if len(normalized) > MAX_PROMPT_LENGTH:
            raise PromptTooLongError
        object.__setattr__(self, "value", normalized)
