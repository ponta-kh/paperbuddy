from typing import Protocol

from src.application.use_cases.chat.list_chats.list_chats_dto import (
    ListChatsInput,
    ListChatsOutput,
)


class ListChatsProtocol(Protocol):
    """チャット一覧取得ユースケースの入力ポート。"""

    async def execute(self, query: ListChatsInput) -> ListChatsOutput:
        """指定ユーザーに紐づくチャット一覧を返す。"""
        ...
