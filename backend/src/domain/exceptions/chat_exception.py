from src.domain.exceptions.base import DomainError


class InvalidChatIdError(DomainError):
    pass


class InvalidSessionIdError(DomainError):
    pass


class InvalidPromptError(DomainError):
    pass


class PromptTooLongError(DomainError):
    pass


class InvalidMessageSenderError(DomainError):
    pass


class InvalidChatTurnError(DomainError):
    pass


class MessageSentAtOutOfOrderError(DomainError):
    pass
