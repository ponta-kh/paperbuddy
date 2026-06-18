from dataclasses import dataclass

from src.domain.exceptions.chat_exception import InvalidPromptError, PromptTooLongError

MAX_PROMPT_LENGTH = 1000


@dataclass(frozen=True, slots=True)
class Prompt:
    """ユーザーが入力した質問文を表すValue Object。

    前後空白を除去した後、空文字と最大文字数超過を不正な質問として扱う。
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidPromptError
        if len(normalized) > MAX_PROMPT_LENGTH:
            raise PromptTooLongError
        # frozenなValue Objectとして扱うため、
        # 生成時だけ正規化後の値に差し替える。
        object.__setattr__(self, "value", normalized)
