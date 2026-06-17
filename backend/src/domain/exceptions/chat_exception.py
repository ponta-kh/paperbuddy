from src.domain.exceptions.base import DomainError


class InvalidChatIdError(DomainError):
    """チャットIDがDomainの不変条件を満たさない場合の例外。"""

    pass


class InvalidSessionIdError(DomainError):
    """LLMセッションIDがDomainの不変条件を満たさない場合の例外。"""

    pass


class InvalidPromptError(DomainError):
    """質問文が空など、質問として扱えない場合の例外。"""

    pass


class PromptTooLongError(DomainError):
    """質問文が許容文字数を超過した場合の例外。"""

    pass


class InvalidMessageSenderError(DomainError):
    """メッセージ発信者と内容の組み合わせが不正な場合の例外。"""

    pass


class InvalidChatCitationError(DomainError):
    """引用情報がDomainの不変条件を満たさない場合の例外。"""

    pass


class InvalidChatTurnError(DomainError):
    """ユーザー質問とLLM回答のターン対応が不正な場合の例外。"""

    pass


class MessageSentAtOutOfOrderError(DomainError):
    """チャットメッセージの送信時刻が時系列として不正な場合の例外。"""

    pass


class ChatContinuationExpiredError(DomainError):
    """チャットの継続可能期間を超過した場合の例外。"""

    pass


class ChatOwnershipMismatchError(DomainError):
    """チャット所有者以外が操作しようとした場合の例外。"""

    pass
