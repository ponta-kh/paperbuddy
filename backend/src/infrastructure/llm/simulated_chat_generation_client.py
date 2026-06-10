import asyncio
from uuid import uuid4

from src.application.ports.out.chat_generation_client_protocol import (
    ContinueGeneratedChatResult,
    StartGeneratedChatResult,
)

_ANSWER_SEED = """""
    これはローカル動作確認用の疑似回答です。
    実際のLLMやKnowledge Baseには接続せず、画面表示、待機状態、履歴保存、
    チャット継続の一連の挙動を確認するために固定文を返しています。
    """


class SimulatedChatGenerationClient:
    def __init__(self, *, delay_seconds: float = 2.0) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        self._delay_seconds = delay_seconds

    async def start_chat(self, prompt: str) -> StartGeneratedChatResult:
        await asyncio.sleep(self._delay_seconds)
        return StartGeneratedChatResult(
            session_id=f"local-{uuid4()}",
            answer=self._answer(),
            title=f"{prompt[:10]}...",
        )

    async def continue_chat(
        self, session_id: str, prompt: str
    ) -> ContinueGeneratedChatResult:
        await asyncio.sleep(self._delay_seconds)
        return ContinueGeneratedChatResult(session_id=session_id, answer=self._answer())

    @staticmethod
    def _answer() -> str:
        repeat_count = 300 // len(_ANSWER_SEED) + 1
        return (_ANSWER_SEED * repeat_count)[:300]
