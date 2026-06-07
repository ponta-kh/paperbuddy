import asyncio
from dataclasses import dataclass
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationUnavailableError,
    InvalidChatGenerationResponseError,
    StartGeneratedChatResult,
)


@dataclass(frozen=True, slots=True)
class _KnowledgeBaseChatResult:
    chat_id: str
    answer: str


class BedrockKnowledgeBaseChatClient:
    def __init__(
        self,
        knowledge_base_client: Any,
        model_client: Any,
        *,
        knowledge_base_id: str,
        model_arn: str,
    ) -> None:
        self._knowledge_base_client = knowledge_base_client
        self._model_client = model_client
        self._knowledge_base_id = knowledge_base_id
        self._model_arn = model_arn

    async def start_chat(self, prompt: str) -> StartGeneratedChatResult:
        chat_result, title_result = await asyncio.gather(
            self._start_knowledge_base_chat(prompt),
            self._generate_title(prompt),
            return_exceptions=True,
        )
        if isinstance(chat_result, Exception):
            raise chat_result

        title = (
            self._fallback_title(prompt)
            if isinstance(title_result, Exception)
            else title_result
        )
        return StartGeneratedChatResult(
            chat_id=chat_result.chat_id,
            answer=chat_result.answer,
            title=title,
        )

    async def _start_knowledge_base_chat(self, prompt: str) -> _KnowledgeBaseChatResult:
        try:
            response = await asyncio.to_thread(
                self._knowledge_base_client.retrieve_and_generate,
                input={"text": prompt},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self._knowledge_base_id,
                        "modelArn": self._model_arn,
                    },
                },
            )
        except (BotoCoreError, ClientError) as error:
            raise ChatGenerationUnavailableError from error

        try:
            chat_id = response["sessionId"]
            answer = response["output"]["text"]
            if not all(
                isinstance(value, str) and value.strip() for value in (chat_id, answer)
            ):
                raise ValueError
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidChatGenerationResponseError from error

        return _KnowledgeBaseChatResult(chat_id=chat_id, answer=answer)

    async def _generate_title(self, prompt: str) -> str:
        response = await asyncio.to_thread(
            self._model_client.converse,
            modelId=self._model_arn,
            system=[
                {
                    "text": (
                        "ユーザーの質問に対するチャットタイトルを日本語で生成してください。"
                        "タイトルだけを簡潔に返してください。"
                    )
                }
            ],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 40, "temperature": 0},
        )
        try:
            title = response["output"]["message"]["content"][0]["text"].strip()
            if not title:
                raise ValueError
            return title
        except (KeyError, TypeError, ValueError, IndexError) as error:
            raise InvalidChatGenerationResponseError from error

    @staticmethod
    def _fallback_title(prompt: str) -> str:
        return f"{prompt[:10]}..."
