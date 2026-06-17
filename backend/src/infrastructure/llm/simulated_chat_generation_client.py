import asyncio
from textwrap import dedent
from uuid import uuid7

from src.application.ports.out.chat_generation_client_protocol import (
    ContinueGeneratedChatResult,
    StartGeneratedChatResult,
)

_ANSWER = dedent(
    """\
    これはローカル動作確認用の疑似回答です。
    実際のLLMやKnowledge Baseには接続せず、画面表示、待機状態、履歴保存、
    チャット継続の一連の挙動を確認するために固定文を返しています。
    """
).strip()


class SimulatedChatGenerationClient:
    def __init__(self, *, delay_seconds: float = 2.0) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        self._delay_seconds = delay_seconds

    async def start_chat(self, prompt: str) -> StartGeneratedChatResult:
        await asyncio.sleep(self._delay_seconds)
        return StartGeneratedChatResult(
            session_id=f"local-{uuid7()}",
            answer=self._answer(),
            citations=(),
        )

    async def continue_chat(
        self, session_id: str, prompt: str
    ) -> ContinueGeneratedChatResult:
        await asyncio.sleep(self._delay_seconds)
        return ContinueGeneratedChatResult(
            session_id=session_id,
            answer=self._answer(),
            citations=(),
        )

    @staticmethod
    def _answer() -> str:
        return _ANSWER
