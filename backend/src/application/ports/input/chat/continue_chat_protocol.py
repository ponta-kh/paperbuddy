from typing import Protocol

from src.application.use_cases.chat.continue_chat.continue_chat_dto import (
    ContinueChatInput,
    ContinueChatOutput,
)


class ContinueChatProtocol(Protocol):
    """チャット継続ユースケースの入力ポート。"""

    async def execute(self, command: ContinueChatInput) -> ContinueChatOutput:
        """既存チャットへ質問を追加し、継続LLM回答を返す。"""
        ...
