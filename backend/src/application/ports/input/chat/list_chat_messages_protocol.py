from typing import Protocol

from src.application.use_cases.chat.list_chat_messages.list_chat_messages_dto import (
    ListChatMessagesInput,
    ListChatMessagesOutput,
)


class ListChatMessagesProtocol(Protocol):
    """チャットメッセージ履歴取得ユースケースの入力ポート。"""

    async def execute(self, query: ListChatMessagesInput) -> ListChatMessagesOutput:
        """指定チャットのメッセージ履歴を返す。"""
        ...
