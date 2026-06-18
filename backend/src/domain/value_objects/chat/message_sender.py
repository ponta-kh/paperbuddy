from enum import StrEnum


class MessageSender(StrEnum):
    """チャットメッセージの発信者種別。"""

    USER = "user"
    LLM = "llm"
