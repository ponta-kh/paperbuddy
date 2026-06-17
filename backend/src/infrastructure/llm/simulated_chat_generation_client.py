import asyncio
from textwrap import dedent
from uuid import uuid7

from src.application.ports.out.chat_generation_client_protocol import (
    ContinueGeneratedChatResult,
    GeneratedChatCitation,
    GeneratedChatCitationSource,
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
            citations=self._citations(),
        )

    async def continue_chat(
        self, session_id: str, prompt: str
    ) -> ContinueGeneratedChatResult:
        await asyncio.sleep(self._delay_seconds)
        return ContinueGeneratedChatResult(
            session_id=session_id,
            answer=self._answer(),
            citations=self._citations(),
        )

    @staticmethod
    def _answer() -> str:
        return _ANSWER

    @staticmethod
    def _citations() -> tuple[GeneratedChatCitation, ...]:
        return (
            GeneratedChatCitation(
                text="これはローカル動作確認用の疑似回答です。",
                span_start=0,
                span_end=20,
                sources=(
                    GeneratedChatCitationSource(
                        content=(
                            "PaperBuddyのローカル動作確認では、Knowledge Baseへ接続せず、"
                            "画面表示とチャット継続の挙動を確認するための固定回答を返す。"
                        ),
                        location_type="S3",
                        uri="s3://paperbuddy-local-rag-sources/sample-paper.pdf",
                        metadata={
                            "title": "PaperBuddy ローカル検証用サンプル論文",
                            "file_name": "sample-paper.pdf",
                            "page": 1,
                            "source": "local-simulation",
                        },
                    ),
                ),
            ),
            GeneratedChatCitation(
                text="画面表示、待機状態、履歴保存、チャット継続の一連の挙動を確認するために固定文を返しています。",
                span_start=53,
                span_end=102,
                sources=(
                    GeneratedChatCitationSource(
                        content=(
                            "疑似LLMクライアントは、送信中表示、回答の段階表示、"
                            "履歴保存後のUI更新を本番に近いレスポンス形式で確認する目的で使用する。"
                        ),
                        location_type="S3",
                        uri="s3://paperbuddy-local-rag-sources/chat-flow-guide.pdf",
                        metadata={
                            "title": "チャット動作確認ガイド",
                            "file_name": "chat-flow-guide.pdf",
                            "page": 4,
                            "source": "local-simulation",
                        },
                    ),
                ),
            ),
        )
