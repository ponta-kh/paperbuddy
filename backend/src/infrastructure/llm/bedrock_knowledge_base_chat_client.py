import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationConfigurationError,
    ChatGenerationPermissionDeniedError,
    ChatGenerationRateLimitError,
    ChatGenerationSessionUnavailableError,
    ChatGenerationUnavailableError,
    ContinueGeneratedChatResult,
    InvalidChatGenerationResponseError,
    StartGeneratedChatResult,
)

logger = logging.getLogger(__name__)

_RATE_LIMIT_ERROR_CODES = {
    "ThrottlingException",
    "TooManyRequestsException",
    "ServiceQuotaExceededException",
}
_PERMISSION_ERROR_CODES = {
    "AccessDeniedException",
    "AccessDenied",
    "UnauthorizedException",
}
_CONFIGURATION_ERROR_CODES = {
    "ResourceNotFoundException",
    "ValidationException",
    "ConflictException",
}
_UNAVAILABLE_CLIENT_ERROR_CODES = {
    "BadGatewayException",
    "DependencyFailedException",
    "InternalServerException",
    "ModelTimeoutException",
    "ServiceUnavailableException",
}


@dataclass(frozen=True, slots=True)
class _KnowledgeBaseChatResult:
    session_id: str
    answer: str


class BedrockKnowledgeBaseChatClient:
    def __init__(
        self,
        knowledge_base_client: Any,
        *,
        knowledge_base_id: str,
        model_arn: str,
    ) -> None:
        self._knowledge_base_client = knowledge_base_client
        self._knowledge_base_id = knowledge_base_id
        self._model_arn = model_arn

    async def start_chat(self, prompt: str) -> StartGeneratedChatResult:
        chat_result = await self._start_knowledge_base_chat(prompt)
        return StartGeneratedChatResult(
            session_id=chat_result.session_id,
            answer=chat_result.answer,
        )

    async def continue_chat(
        self, session_id: str, prompt: str
    ) -> ContinueGeneratedChatResult:
        result = await self._continue_knowledge_base_chat(session_id, prompt)
        return ContinueGeneratedChatResult(
            session_id=result.session_id, answer=result.answer
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
        except ClientError as error:
            self._raise_client_error(
                error,
                operation="start_chat",
                validation_error=ChatGenerationConfigurationError,
            )
        except BotoCoreError as error:
            logger.exception(
                "Bedrock Knowledge Baseへの接続に失敗しました",
                extra={
                    "event": "bedrock_knowledge_base_unavailable",
                    "operation": "start_chat",
                },
            )
            raise ChatGenerationUnavailableError from error

        try:
            session_id = response["sessionId"]
            answer = response["output"]["text"]
            if not all(
                isinstance(value, str) and value.strip()
                for value in (session_id, answer)
            ):
                raise ValueError
        except (KeyError, TypeError, ValueError) as error:
            logger.warning(
                "Bedrock Knowledge Baseの回答生成レスポンスが不正です",
                extra={"event": "bedrock_knowledge_base_invalid_response"},
            )
            raise InvalidChatGenerationResponseError from error

        return _KnowledgeBaseChatResult(session_id=session_id, answer=answer)

    async def _continue_knowledge_base_chat(
        self, session_id: str, prompt: str
    ) -> _KnowledgeBaseChatResult:
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
                sessionId=session_id,
            )
        except ClientError as error:
            self._raise_client_error(
                error,
                operation="continue_chat",
                validation_error=ChatGenerationSessionUnavailableError,
            )
        except BotoCoreError as error:
            logger.exception(
                "Bedrock Knowledge Baseへの接続に失敗しました",
                extra={
                    "event": "bedrock_knowledge_base_unavailable",
                    "operation": "continue_chat",
                },
            )
            raise ChatGenerationUnavailableError from error

        try:
            returned_session_id = response["sessionId"]
            answer = response["output"]["text"]
            if (
                returned_session_id != session_id
                or not isinstance(answer, str)
                or not answer.strip()
            ):
                raise ValueError
        except (KeyError, TypeError, ValueError) as error:
            logger.warning(
                "Bedrock Knowledge Baseの継続回答生成レスポンスが不正です",
                extra={"event": "bedrock_knowledge_base_invalid_continue_response"},
            )
            raise InvalidChatGenerationResponseError from error

        return _KnowledgeBaseChatResult(session_id=returned_session_id, answer=answer)

    @staticmethod
    def _client_error_code(error: ClientError) -> str:
        code = error.response.get("Error", {}).get("Code")
        if isinstance(code, str) and code:
            return code
        return "Unknown"

    @staticmethod
    def _client_error_message(error: ClientError) -> str:
        message = error.response.get("Error", {}).get("Message")
        if isinstance(message, str):
            return message
        return ""

    @classmethod
    def _raise_client_error(
        cls,
        error: ClientError,
        *,
        operation: str,
        validation_error: type[Exception],
    ) -> None:
        error_code = cls._client_error_code(error)
        if error_code in _RATE_LIMIT_ERROR_CODES:
            logger.warning(
                "Bedrock Knowledge Baseの呼び出しが制限されました",
                extra={
                    "event": "bedrock_knowledge_base_rate_limited",
                    "operation": operation,
                    "error_code": error_code,
                },
            )
            raise ChatGenerationRateLimitError from error
        if error_code in _PERMISSION_ERROR_CODES:
            logger.exception(
                "Bedrock Knowledge Baseの呼び出し権限がありません",
                extra={
                    "event": "bedrock_knowledge_base_permission_denied",
                    "operation": operation,
                    "error_code": error_code,
                },
            )
            raise ChatGenerationPermissionDeniedError from error
        if (
            error_code == "ValidationException"
            and validation_error is ChatGenerationSessionUnavailableError
            and "session" in cls._client_error_message(error).lower()
        ):
            logger.warning(
                "Bedrock Knowledge Baseのセッションを継続できません",
                extra={
                    "event": "bedrock_knowledge_base_session_unavailable",
                    "operation": operation,
                    "error_code": error_code,
                },
            )
            raise ChatGenerationSessionUnavailableError from error
        if error_code in _CONFIGURATION_ERROR_CODES:
            logger.exception(
                "Bedrock Knowledge Baseの呼び出し設定が不正です",
                extra={
                    "event": "bedrock_knowledge_base_configuration_error",
                    "operation": operation,
                    "error_code": error_code,
                },
            )
            if validation_error is ChatGenerationSessionUnavailableError:
                raise ChatGenerationConfigurationError from error
            raise validation_error from error

        if error_code in _UNAVAILABLE_CLIENT_ERROR_CODES:
            logger.exception(
                "Bedrock Knowledge Baseが利用できません",
                extra={
                    "event": "bedrock_knowledge_base_unavailable",
                    "operation": operation,
                    "error_code": error_code,
                },
            )
            raise ChatGenerationUnavailableError from error

        logger.exception(
            "Bedrock Knowledge Baseによる回答生成に失敗しました",
            extra={
                "event": "bedrock_knowledge_base_unavailable",
                "operation": operation,
                "error_code": error_code,
            },
        )
        raise ChatGenerationUnavailableError from error
