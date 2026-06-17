import asyncio
import logging
from dataclasses import dataclass
from typing import Any, cast

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
_AUTHENTICATION_ERROR_CODES = {
    "ExpiredTokenException",
    "InvalidClientTokenId",
    "UnrecognizedClientException",
}


@dataclass(frozen=True, slots=True)
class _BedrockErrorHint:
    event: str
    message: str
    diagnosis: str
    remediation: str


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
        response = cast(dict[str, Any], error.response)
        error_body = response.get("Error")
        if not isinstance(error_body, dict):
            return "Unknown"
        code = error_body.get("Code")
        if isinstance(code, str) and code:
            return code
        return "Unknown"

    @staticmethod
    def _client_error_message(error: ClientError) -> str:
        response = cast(dict[str, Any], error.response)
        error_body = response.get("Error")
        if not isinstance(error_body, dict):
            return ""
        message = error_body.get("Message")
        if isinstance(message, str):
            return message
        return ""

    @classmethod
    def _configuration_error_hint(
        cls, error_code: str, error_message: str
    ) -> _BedrockErrorHint:
        normalized_message = error_message.lower()
        if "on-demand throughput" in normalized_message:
            return _BedrockErrorHint(
                event="bedrock_knowledge_base_model_requires_inference_profile",
                message="Bedrock Knowledge Baseのモデル指定にInference Profileが必要です",
                diagnosis=(
                    "指定したモデルはオンデマンド呼び出しに対応していません。"
                    "RetrieveAndGenerateには対象モデルを含むInference ProfileのIDまたはARNを指定してください。"
                ),
                remediation=(
                    "BEDROCK_MODEL_ARNにInference Profile ID/ARNを設定するか、"
                    "オンデマンド対応モデルへ変更してください。"
                ),
            )
        if "marked by provider as legacy" in normalized_message:
            return _BedrockErrorHint(
                event="bedrock_knowledge_base_model_legacy",
                message="Bedrock Knowledge BaseのモデルがLegacy扱いで利用できません",
                diagnosis=(
                    "指定したモデルはプロバイダーによりLegacy扱いになっており、"
                    "現在のアカウントではRetrieveAndGenerateに利用できません。"
                ),
                remediation="BEDROCK_MODEL_ARNをActiveなモデルまたはInference Profileへ変更してください。",
            )
        if "custom prompt templates must be provided" in normalized_message:
            return _BedrockErrorHint(
                event="bedrock_knowledge_base_model_requires_custom_prompt",
                message="Bedrock Knowledge Baseのモデルにカスタムプロンプト設定が必要です",
                diagnosis=(
                    "指定したモデルはKnowledge Baseのデフォルトプロンプトでは利用できません。"
                    "OrchestrationとGenerationの両方にカスタムプロンプトテンプレートが必要です。"
                ),
                remediation=(
                    "デフォルトプロンプトで動くモデルへ変更するか、"
                    "RetrieveAndGenerate設定へOrchestration/GenerationのpromptTemplateを追加してください。"
                ),
            )
        if "modelarn" in normalized_message or "model arn" in normalized_message:
            return _BedrockErrorHint(
                event="bedrock_knowledge_base_invalid_model_identifier",
                message="Bedrock Knowledge Baseのモデル指定が不正です",
                diagnosis=(
                    "BEDROCK_MODEL_ARNにBedrockモデルまたはInference Profileではない値が指定されています。"
                    "OpenSearch Serverless Collection ARNなどは指定できません。"
                ),
                remediation=(
                    "BEDROCK_MODEL_ARNにはBedrock foundation model ARN、"
                    "model ID、Inference Profile ID/ARNのいずれかを設定してください。"
                ),
            )
        if "knowledgebase" in normalized_message or "knowledge base" in normalized_message:
            return _BedrockErrorHint(
                event="bedrock_knowledge_base_invalid_knowledge_base",
                message="Bedrock Knowledge Base IDが不正です",
                diagnosis="BEDROCK_KNOWLEDGE_BASE_IDが存在しない、またはリージョン/アカウントと一致していません。",
                remediation="対象リージョンのKnowledge Base IDを確認してBEDROCK_KNOWLEDGE_BASE_IDへ設定してください。",
            )
        return _BedrockErrorHint(
            event="bedrock_knowledge_base_configuration_error",
            message="Bedrock Knowledge Baseの呼び出し設定が不正です",
            diagnosis=(
                "RetrieveAndGenerateの設定がBedrockの制約を満たしていません。"
                "Knowledge Base ID、モデル/Inference Profile、リージョン、プロンプト要件を確認してください。"
            ),
            remediation="Bedrockのエラーメッセージを確認し、.envまたはRetrieveAndGenerate設定を修正してください。",
        )

    @classmethod
    def _raise_client_error(
        cls,
        error: ClientError,
        *,
        operation: str,
        validation_error: type[Exception],
    ) -> None:
        error_code = cls._client_error_code(error)
        error_message = cls._client_error_message(error)
        if error_code in _AUTHENTICATION_ERROR_CODES:
            logger.exception(
                "Bedrock Knowledge BaseのAWS認証情報が無効です",
                extra={
                    "event": "bedrock_knowledge_base_authentication_error",
                    "operation": operation,
                    "error_code": error_code,
                    "diagnosis": (
                        "AWS認証情報が無効、期限切れ、または一時認証のSESSION_TOKENが一致していません。"
                    ),
                    "remediation": (
                        "AWS認証情報を更新し、Docker/ECSへAWS_ACCESS_KEY_ID、"
                        "AWS_SECRET_ACCESS_KEY、必要に応じてAWS_SESSION_TOKENを渡してください。"
                    ),
                },
            )
            raise ChatGenerationUnavailableError(
                "Bedrock Knowledge BaseのAWS認証情報が無効です。"
                "認証情報を更新し、実行環境へ正しく渡してください。"
            ) from error
        if error_code in _RATE_LIMIT_ERROR_CODES:
            logger.warning(
                "Bedrock Knowledge Baseの呼び出しが制限されました",
                extra={
                    "event": "bedrock_knowledge_base_rate_limited",
                    "operation": operation,
                    "error_code": error_code,
                },
            )
            raise ChatGenerationRateLimitError(
                "Bedrock Knowledge Baseの呼び出しが制限されました。"
                "クォータまたはレート制限を確認してください。"
            ) from error
        if error_code in _PERMISSION_ERROR_CODES:
            logger.exception(
                "Bedrock Knowledge Baseの呼び出し権限がありません",
                extra={
                    "event": "bedrock_knowledge_base_permission_denied",
                    "operation": operation,
                    "error_code": error_code,
                    "diagnosis": "実行ロールまたはユーザーにBedrock呼び出し権限がありません。",
                    "remediation": (
                        "bedrock:RetrieveAndGenerate と対象モデル/Inference Profileの"
                        "bedrock:InvokeModel 権限を確認してください。"
                    ),
                },
            )
            raise ChatGenerationPermissionDeniedError(
                "Bedrock Knowledge Baseの呼び出し権限がありません。"
                "IAMポリシーと対象リソースを確認してください。"
            ) from error
        if (
            error_code == "ValidationException"
            and validation_error is ChatGenerationSessionUnavailableError
            and "session" in error_message.lower()
        ):
            logger.warning(
                "Bedrock Knowledge Baseのセッションを継続できません",
                extra={
                    "event": "bedrock_knowledge_base_session_unavailable",
                    "operation": operation,
                    "error_code": error_code,
                },
            )
            raise ChatGenerationSessionUnavailableError(
                "Bedrock Knowledge Baseのセッションを継続できません。"
                "セッション期限切れまたは不正なsessionIdです。"
            ) from error
        if error_code in _CONFIGURATION_ERROR_CODES:
            hint = cls._configuration_error_hint(error_code, error_message)
            logger.exception(
                hint.message,
                extra={
                    "event": hint.event,
                    "operation": operation,
                    "error_code": error_code,
                    "diagnosis": hint.diagnosis,
                    "remediation": hint.remediation,
                },
            )
            exception_message = f"{hint.diagnosis} 対応: {hint.remediation}"
            if validation_error is ChatGenerationSessionUnavailableError:
                raise ChatGenerationConfigurationError(exception_message) from error
            raise validation_error(exception_message) from error

        if error_code in _UNAVAILABLE_CLIENT_ERROR_CODES:
            logger.exception(
                "Bedrock Knowledge Baseが利用できません",
                extra={
                    "event": "bedrock_knowledge_base_unavailable",
                    "operation": operation,
                    "error_code": error_code,
                },
            )
            raise ChatGenerationUnavailableError(
                "Bedrock Knowledge Baseが一時的に利用できません。時間を置いて再試行してください。"
            ) from error

        logger.exception(
            "Bedrock Knowledge Baseによる回答生成に失敗しました",
            extra={
                "event": "bedrock_knowledge_base_unavailable",
                "operation": operation,
                "error_code": error_code,
            },
        )
        raise ChatGenerationUnavailableError(
            "Bedrock Knowledge Baseによる回答生成に失敗しました。"
            "error_codeとBedrockのエラーメッセージを確認してください。"
        ) from error
