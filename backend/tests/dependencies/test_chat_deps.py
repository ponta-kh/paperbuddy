from collections.abc import Iterator
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from src.application.use_cases.chat.delete_chat.delete_chat import DeleteChatUseCase
from src.application.use_cases.chat.rename_chat.rename_chat import RenameChatUseCase
from src.dependencies import chat_deps
from src.dependencies.settings import get_settings
from src.infrastructure.llm.bedrock_knowledge_base_chat_client import (
    BedrockKnowledgeBaseChatClient,
)
from src.infrastructure.llm.simulated_chat_generation_client import (
    SimulatedChatGenerationClient,
)
from src.infrastructure.repositories.chat.dynamodb_chat_repository import (
    DynamoDbChatRepository,
)


@pytest.fixture(autouse=True)
def clear_cached_dependencies() -> Iterator[None]:
    chat_deps.get_chat_repository.cache_clear()
    chat_deps.get_chat_generation_client.cache_clear()
    chat_deps.get_rename_chat_use_case.cache_clear()
    chat_deps.get_delete_chat_use_case.cache_clear()
    get_settings.cache_clear()
    yield
    chat_deps.get_chat_repository.cache_clear()
    chat_deps.get_chat_generation_client.cache_clear()
    chat_deps.get_rename_chat_use_case.cache_clear()
    chat_deps.get_delete_chat_use_case.cache_clear()
    get_settings.cache_clear()


def _set_aws_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv("DYNAMODB_CHAT_TABLE_NAME", "chat-table")
    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "knowledge-base-id")
    monkeypatch.setenv("BEDROCK_MODEL_ARN", "model-arn")


def _set_local_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAT_INFRASTRUCTURE_MODE", "local")
    monkeypatch.setenv("AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv("DYNAMODB_CHAT_TABLE_NAME", "chat-table")
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", "http://dynamodb-local:8000")


def test_get_chat_repository_uses_dynamodb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_aws_environment(monkeypatch)
    dynamodb_client = Mock()
    client_factory = Mock(return_value=dynamodb_client)
    monkeypatch.setattr(chat_deps.boto3, "client", client_factory)

    repository = chat_deps.get_chat_repository()

    assert isinstance(repository, DynamoDbChatRepository)
    assert client_factory.call_args == (
        ("dynamodb",),
        {"region_name": "ap-northeast-1"},
    )


def test_get_chat_command_use_cases_use_dynamodb_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_aws_environment(monkeypatch)
    monkeypatch.setattr(chat_deps.boto3, "client", Mock())

    assert isinstance(chat_deps.get_rename_chat_use_case(), RenameChatUseCase)
    assert isinstance(chat_deps.get_delete_chat_use_case(), DeleteChatUseCase)


def test_get_chat_repository_uses_dynamodb_local_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_local_environment(monkeypatch)
    dynamodb_client = Mock()
    client_factory = Mock(return_value=dynamodb_client)
    monkeypatch.setattr(chat_deps.boto3, "client", client_factory)

    repository = chat_deps.get_chat_repository()

    assert isinstance(repository, DynamoDbChatRepository)
    assert client_factory.call_args == (
        ("dynamodb",),
        {
            "region_name": "ap-northeast-1",
            "endpoint_url": "http://dynamodb-local:8000",
        },
    )


@pytest.mark.parametrize("missing_name", ["AWS_REGION", "DYNAMODB_CHAT_TABLE_NAME"])
def test_get_chat_repository_rejects_missing_environment(
    monkeypatch: pytest.MonkeyPatch,
    missing_name: str,
) -> None:
    _set_aws_environment(monkeypatch)
    monkeypatch.delenv(missing_name)

    with pytest.raises(ValidationError, match=missing_name.lower()):
        chat_deps.get_chat_repository()


def test_get_chat_generation_client_uses_bedrock_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_aws_environment(monkeypatch)
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


def test_get_chat_generation_client_uses_simulated_client_locally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_local_environment(monkeypatch)
    monkeypatch.setenv("SIMULATED_LLM_DELAY_SECONDS", "0")

    client = chat_deps.get_chat_generation_client()

    assert isinstance(client, SimulatedChatGenerationClient)


def test_rejects_unknown_infrastructure_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_aws_environment(monkeypatch)
    monkeypatch.setenv("CHAT_INFRASTRUCTURE_MODE", "unknown")

    with pytest.raises(ValidationError, match="chat_infrastructure_mode"):
        chat_deps.get_chat_repository()


@pytest.mark.parametrize(
    "missing_name",
    ["AWS_REGION", "BEDROCK_KNOWLEDGE_BASE_ID", "BEDROCK_MODEL_ARN"],
)
def test_get_chat_generation_client_rejects_missing_required_environment(
    monkeypatch: pytest.MonkeyPatch,
    missing_name: str,
) -> None:
    _set_aws_environment(monkeypatch)
    monkeypatch.delenv(missing_name)

    expected_message = (
        missing_name.lower() if missing_name == "AWS_REGION" else missing_name
    )
    with pytest.raises(ValidationError, match=expected_message):
        chat_deps.get_chat_generation_client()
