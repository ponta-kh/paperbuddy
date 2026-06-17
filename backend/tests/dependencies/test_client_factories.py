from unittest.mock import Mock

import pytest

from src.dependencies import client_factories
from src.dependencies.settings import (
    ChatGenerationMode,
    ChatInfrastructureMode,
    Settings,
)
from src.infrastructure.llm.bedrock_knowledge_base_chat_client import (
    BedrockKnowledgeBaseChatClient,
)
from src.infrastructure.llm.simulated_chat_generation_client import (
    SimulatedChatGenerationClient,
)


def test_create_dynamodb_client_uses_aws_region(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock()
    boto3_client = Mock(return_value=client)
    monkeypatch.setattr(client_factories.boto3, "client", boto3_client)

    result = client_factories.create_dynamodb_client(_aws_settings())

    assert result is client
    boto3_client.assert_called_once_with("dynamodb", region_name="ap-northeast-1")


def test_create_dynamodb_client_uses_local_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock()
    boto3_client = Mock(return_value=client)
    monkeypatch.setattr(client_factories.boto3, "client", boto3_client)

    result = client_factories.create_dynamodb_client(_local_settings())

    assert result is client
    boto3_client.assert_called_once_with(
        "dynamodb",
        region_name="ap-northeast-1",
        endpoint_url="http://dynamodb-local:8000",
    )


def test_create_chat_generation_client_uses_simulated_client_locally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boto3_client = Mock()
    monkeypatch.setattr(client_factories.boto3, "client", boto3_client)

    result = client_factories.create_chat_generation_client(_local_settings())

    assert isinstance(result, SimulatedChatGenerationClient)
    boto3_client.assert_not_called()


def test_create_chat_generation_client_uses_bedrock_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    knowledge_base_client = Mock()
    boto3_client = Mock(return_value=knowledge_base_client)
    monkeypatch.setattr(client_factories.boto3, "client", boto3_client)

    result = client_factories.create_chat_generation_client(_aws_settings())

    assert isinstance(result, BedrockKnowledgeBaseChatClient)
    assert boto3_client.call_args_list == [
        (("bedrock-agent-runtime",), {"region_name": "ap-northeast-1"}),
    ]


def test_create_chat_generation_client_uses_bedrock_with_local_dynamodb_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    knowledge_base_client = Mock()
    boto3_client = Mock(return_value=knowledge_base_client)
    monkeypatch.setattr(client_factories.boto3, "client", boto3_client)

    result = client_factories.create_chat_generation_client(_local_bedrock_settings())

    assert isinstance(result, BedrockKnowledgeBaseChatClient)
    assert boto3_client.call_args_list == [
        (("bedrock-agent-runtime",), {"region_name": "ap-northeast-1"}),
    ]


def _aws_settings() -> Settings:
    return Settings(
        aws_region="ap-northeast-1",
        dynamodb_chat_table_name="chat-table",
        dynamodb_library_table_name="library-table",
        bedrock_knowledge_base_id="knowledge-base-id",
        bedrock_model_arn="model-arn",
    )


def _local_settings() -> Settings:
    return Settings(
        chat_infrastructure_mode=ChatInfrastructureMode.LOCAL,
        aws_region="ap-northeast-1",
        dynamodb_chat_table_name="chat-table",
        dynamodb_library_table_name="library-table",
        dynamodb_endpoint_url="http://dynamodb-local:8000",
        simulated_llm_delay_seconds=0,
    )


def _local_bedrock_settings() -> Settings:
    return Settings(
        chat_infrastructure_mode=ChatInfrastructureMode.LOCAL,
        chat_generation_mode=ChatGenerationMode.AWS,
        aws_region="ap-northeast-1",
        dynamodb_chat_table_name="chat-table",
        dynamodb_library_table_name="library-table",
        dynamodb_endpoint_url="http://dynamodb-local:8000",
        bedrock_knowledge_base_id="knowledge-base-id",
        bedrock_model_arn="model-arn",
    )
