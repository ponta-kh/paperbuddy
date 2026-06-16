from typing import Any

import boto3

from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
)
from src.dependencies.settings import Settings
from src.infrastructure.llm.bedrock_knowledge_base_chat_client import (
    BedrockKnowledgeBaseChatClient,
)
from src.infrastructure.llm.simulated_chat_generation_client import (
    SimulatedChatGenerationClient,
)


def create_dynamodb_client(settings: Settings) -> Any:
    client_options: dict[str, str] = {"region_name": settings.aws_region}
    if settings.is_local_mode:
        assert settings.dynamodb_endpoint_url is not None
        client_options["endpoint_url"] = settings.dynamodb_endpoint_url
    return boto3.client("dynamodb", **client_options)


def create_chat_generation_client(settings: Settings) -> ChatGenerationClientProtocol:
    if settings.is_local_mode:
        return SimulatedChatGenerationClient(
            delay_seconds=settings.simulated_llm_delay_seconds
        )

    assert settings.bedrock_knowledge_base_id is not None
    assert settings.bedrock_model_arn is not None
    knowledge_base_client = boto3.client(
        "bedrock-agent-runtime", region_name=settings.aws_region
    )
    model_client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    return BedrockKnowledgeBaseChatClient(
        knowledge_base_client,
        model_client,
        knowledge_base_id=settings.bedrock_knowledge_base_id,
        model_arn=settings.bedrock_model_arn,
    )
