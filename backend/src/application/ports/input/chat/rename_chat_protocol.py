from typing import Protocol

from src.application.use_cases.chat.rename_chat.rename_chat_dto import (
    RenameChatInput,
    RenameChatOutput,
)


class RenameChatProtocol(Protocol):
    """チャットタイトル変更ユースケースの入力ポート。"""

    async def execute(self, command: RenameChatInput) -> RenameChatOutput:
        """指定ユーザーに紐づくチャットタイトルを変更する。"""
        ...
