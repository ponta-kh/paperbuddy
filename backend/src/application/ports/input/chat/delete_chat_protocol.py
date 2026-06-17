from typing import Protocol

from src.application.use_cases.chat.delete_chat.delete_chat_dto import DeleteChatInput


class DeleteChatProtocol(Protocol):
    """チャット削除ユースケースの入力ポート。"""

    async def execute(self, command: DeleteChatInput) -> None:
        """指定ユーザーに紐づくチャットを削除する。"""
        ...
