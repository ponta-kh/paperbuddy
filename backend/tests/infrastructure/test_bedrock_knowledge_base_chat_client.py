import pytest

from src.application.ports.out.chat_generation_client_protocol import (
    InvalidChatGenerationResponseError,
)
from src.infrastructure.llm.bedrock_knowledge_base_chat_client import (
    BedrockKnowledgeBaseChatClient,
)


class StubKnowledgeBaseClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.request: dict | None = None

    def retrieve_and_generate(self, **kwargs: object) -> dict:
        self.request = kwargs
        return self.response


class StubModelClient:
    def __init__(
        self, response: dict | None = None, error: Exception | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.request: dict | None = None

    def converse(self, **kwargs: object) -> dict:
        self.request = kwargs
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _client(
    knowledge_base: StubKnowledgeBaseClient,
    model: StubModelClient,
) -> BedrockKnowledgeBaseChatClient:
    return BedrockKnowledgeBaseChatClient(
        knowledge_base,
        model,
        knowledge_base_id="knowledge-base-id",
        model_arn="model-arn",
    )


@pytest.mark.asyncio
async def test_start_chat_generates_answer_and_title() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        {"sessionId": "session-1", "output": {"text": "answer"}}
    )
    model = StubModelClient(
        {"output": {"message": {"content": [{"text": " generated title "}]}}}
    )

    result = await _client(knowledge_base, model).start_chat("question")

    assert result.chat_id == "session-1"
    assert result.answer == "answer"
    assert result.title == "generated title"
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
    assert model.request is not None
    assert model.request["modelId"] == "model-arn"
    assert model.request["messages"] == [
        {"role": "user", "content": [{"text": "question"}]}
    ]


@pytest.mark.asyncio
async def test_start_chat_uses_fallback_when_title_generation_fails() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        {"sessionId": "session-1", "output": {"text": "answer"}}
    )
    model = StubModelClient(error=RuntimeError("title generation failed"))

    result = await _client(knowledge_base, model).start_chat("1234567890abcdef")

    assert result.title == "1234567890..."


@pytest.mark.asyncio
async def test_start_chat_uses_fallback_when_title_is_blank() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        {"sessionId": "session-1", "output": {"text": "answer"}}
    )
    model = StubModelClient({"output": {"message": {"content": [{"text": " "}]}}})

    result = await _client(knowledge_base, model).start_chat("question")

    assert result.title == "question..."


@pytest.mark.asyncio
async def test_start_chat_rejects_blank_answer() -> None:
    knowledge_base = StubKnowledgeBaseClient(
        {"sessionId": "session-1", "output": {"text": " "}}
    )
    model = StubModelClient({"output": {"message": {"content": [{"text": "title"}]}}})

    with pytest.raises(InvalidChatGenerationResponseError):
        await _client(knowledge_base, model).start_chat("question")
