from typing import Protocol

from src.application.use_cases.chat.start_chat.start_chat_dto import (
    StartChatInput,
    StartChatOutput,
)


class StartChatProtocol(Protocol):
    """チャット開始ユースケースの入力ポート。"""

    async def execute(self, command: StartChatInput) -> StartChatOutput:
        """新しいチャットを開始し、初回LLM回答を返す。"""
        ...
