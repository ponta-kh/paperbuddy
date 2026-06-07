from collections.abc import Iterator
from unittest.mock import Mock

import pytest

from src.dependencies import chat_deps
from src.infrastructure.llm.bedrock_knowledge_base_chat_client import (
    BedrockKnowledgeBaseChatClient,
)


@pytest.fixture(autouse=True)
def clear_cached_dependencies() -> Iterator[None]:
    chat_deps.get_chat_generation_client.cache_clear()
    yield
    chat_deps.get_chat_generation_client.cache_clear()


def test_get_chat_generation_client_uses_bedrock_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "knowledge-base-id")
    monkeypatch.setenv("BEDROCK_MODEL_ARN", "model-arn")
    knowledge_base_client = Mock()
    model_client = Mock()
    client_factory = Mock(side_effect=[knowledge_base_client, model_client])
    monkeypatch.setattr(chat_deps.boto3, "client", client_factory)

    client = chat_deps.get_chat_generation_client()

    assert isinstance(client, BedrockKnowledgeBaseChatClient)
    assert client_factory.call_args_list == [
        (("bedrock-agent-runtime",), {"region_name": "ap-northeast-1"}),
        (("bedrock-runtime",), {"region_name": "ap-northeast-1"}),
    ]


@pytest.mark.parametrize(
    "missing_name",
    ["AWS_REGION", "BEDROCK_KNOWLEDGE_BASE_ID", "BEDROCK_MODEL_ARN"],
)
def test_get_chat_generation_client_rejects_missing_required_environment(
    monkeypatch: pytest.MonkeyPatch,
    missing_name: str,
) -> None:
    environment = {
        "AWS_REGION": "ap-northeast-1",
        "BEDROCK_KNOWLEDGE_BASE_ID": "knowledge-base-id",
        "BEDROCK_MODEL_ARN": "model-arn",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv(missing_name)

    with pytest.raises(KeyError, match=missing_name):
        chat_deps.get_chat_generation_client()
