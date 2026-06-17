import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationConfigurationError,
    ChatGenerationPermissionDeniedError,
    ChatGenerationRateLimitError,
    ChatGenerationSessionUnavailableError,
    ChatGenerationUnavailableError,
    InvalidChatGenerationResponseError,
)
from src.infrastructure.llm.bedrock_knowledge_base_chat_client import (
    BedrockKnowledgeBaseChatClient,
)


class StubKnowledgeBaseClient:
    def __init__(
        self, response: dict | None = None, error: Exception | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.request: dict | None = None

    def retrieve_and_generate(self, **kwargs: object) -> dict:
        self.request = kwargs
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _client(knowledge_base: StubKnowledgeBaseClient) -> BedrockKnowledgeBaseChatClient:
    return BedrockKnowledgeBaseChatClient(
        knowledge_base,
        knowledge_base_id="knowledge-base-id",
        model_arn="model-arn",
    )


def _client_error(code: str, message: str = "bedrock error") -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "RetrieveAndGenerate",
    )


@pytest.mark.asyncio
async def test_start_chat_generates_answer() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        {"sessionId": "session-1", "output": {"text": "answer"}}
    )

    result = await _client(knowledge_base).start_chat("question")

    assert result.session_id == "session-1"
    assert result.answer == "answer"
    assert knowledge_base.request == {
        "input": {"text": "question"},
        "retrieveAndGenerateConfiguration": {
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": "knowledge-base-id",
                "modelArn": "model-arn",
            },
        },
    }


@pytest.mark.asyncio
async def test_start_chat_raises_permission_denied_for_access_denied(
    caplog: pytest.LogCaptureFixture,
) -> None:
    knowledge_base = StubKnowledgeBaseClient(error=_client_error("AccessDeniedException"))

    with pytest.raises(ChatGenerationPermissionDeniedError):
        await _client(knowledge_base).start_chat("秘密の質問")

    record = caplog.records[0]
    assert getattr(record, "event") == "bedrock_knowledge_base_permission_denied"
    assert getattr(record, "error_code") == "AccessDeniedException"
    assert "秘密の質問" not in caplog.text


@pytest.mark.asyncio
async def test_start_chat_raises_rate_limit_for_throttling() -> None:
    knowledge_base = StubKnowledgeBaseClient(error=_client_error("ThrottlingException"))

    with pytest.raises(ChatGenerationRateLimitError):
        await _client(knowledge_base).start_chat("question")


@pytest.mark.asyncio
async def test_start_chat_raises_configuration_error_for_invalid_request() -> None:
    knowledge_base = StubKnowledgeBaseClient(error=_client_error("ValidationException"))

    with pytest.raises(ChatGenerationConfigurationError):
        await _client(knowledge_base).start_chat("question")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message", "expected_event", "expected_text"),
    [
        (
            "Invocation of model ID model with on-demand throughput isn’t supported.",
            "bedrock_knowledge_base_model_requires_inference_profile",
            "Inference Profile",
        ),
        (
            "This Model is marked by provider as Legacy.",
            "bedrock_knowledge_base_model_legacy",
            "Legacy",
        ),
        (
            "Custom prompt templates must be provided for both Orchestration and Generation.",
            "bedrock_knowledge_base_model_requires_custom_prompt",
            "カスタムプロンプト",
        ),
        (
            "Value 'arn:aws:aoss:collection/example' at modelArn failed to satisfy constraint.",
            "bedrock_knowledge_base_invalid_model_identifier",
            "Bedrockモデル",
        ),
    ],
)
async def test_start_chat_logs_actionable_configuration_error(
    caplog: pytest.LogCaptureFixture,
    message: str,
    expected_event: str,
    expected_text: str,
) -> None:
    knowledge_base = StubKnowledgeBaseClient(
        error=_client_error("ValidationException", message)
    )

    with pytest.raises(ChatGenerationConfigurationError) as error_info:
        await _client(knowledge_base).start_chat("question")

    record = caplog.records[0]
    assert getattr(record, "event") == expected_event
    assert getattr(record, "diagnosis")
    assert getattr(record, "remediation")
    assert expected_text in str(error_info.value)


@pytest.mark.asyncio
async def test_start_chat_logs_authentication_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    knowledge_base = StubKnowledgeBaseClient(
        error=_client_error(
            "ExpiredTokenException",
            "The security token included in the request is expired",
        )
    )

    with pytest.raises(ChatGenerationUnavailableError) as error_info:
        await _client(knowledge_base).start_chat("question")

    record = caplog.records[0]
    assert getattr(record, "event") == "bedrock_knowledge_base_authentication_error"
    assert getattr(record, "diagnosis")
    assert getattr(record, "remediation")
    assert "AWS認証情報が無効" in str(error_info.value)


@pytest.mark.asyncio
async def test_start_chat_raises_unavailable_for_connection_error() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        error=EndpointConnectionError(endpoint_url="bedrock")
    )

    with pytest.raises(ChatGenerationUnavailableError):
        await _client(knowledge_base).start_chat("question")


@pytest.mark.asyncio
async def test_start_chat_rejects_blank_answer() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        {"sessionId": "session-1", "output": {"text": " "}}
    )

    with pytest.raises(InvalidChatGenerationResponseError):
        await _client(knowledge_base).start_chat("question")


@pytest.mark.asyncio
async def test_continue_chat_uses_existing_session() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        {"sessionId": "session-1", "output": {"text": "next answer"}}
    )

    result = await _client(knowledge_base).continue_chat("session-1", "next question")

    assert result.session_id == "session-1"
    assert result.answer == "next answer"
    assert knowledge_base.request == {
        "input": {"text": "next question"},
        "retrieveAndGenerateConfiguration": {
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": "knowledge-base-id",
                "modelArn": "model-arn",
            },
        },
        "sessionId": "session-1",
    }


@pytest.mark.asyncio
async def test_continue_chat_rejects_changed_session_id() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        {"sessionId": "other-session", "output": {"text": "next answer"}}
    )

    with pytest.raises(InvalidChatGenerationResponseError):
        await _client(knowledge_base).continue_chat("session-1", "next question")


@pytest.mark.asyncio
async def test_continue_chat_raises_session_unavailable_for_validation_error() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        error=_client_error("ValidationException", "Session is expired")
    )

    with pytest.raises(ChatGenerationSessionUnavailableError):
        await _client(knowledge_base).continue_chat("session-1", "next question")


@pytest.mark.asyncio
async def test_continue_chat_raises_configuration_error_for_non_session_validation() -> None:
    knowledge_base = StubKnowledgeBaseClient(error=_client_error("ValidationException"))

    with pytest.raises(ChatGenerationConfigurationError):
        await _client(knowledge_base).continue_chat("session-1", "next question")
