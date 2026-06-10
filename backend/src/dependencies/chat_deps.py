from functools import lru_cache

import boto3

from src.application.ports.input.chat.continue_chat_protocol import ContinueChatProtocol
from src.application.ports.input.chat.list_chat_messages_protocol import (
    ListChatMessagesProtocol,
)
from src.application.ports.input.chat.list_chats_protocol import ListChatsProtocol
from src.application.ports.input.chat.start_chat_protocol import (
    StartChatProtocol,
)
from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
)
from src.application.use_cases.chat.continue_chat.continue_chat import (
    ContinueChatUseCase,
)
from src.application.use_cases.chat.list_chat_messages.list_chat_messages import (
    ListChatMessagesUseCase,
)
from src.application.use_cases.chat.list_chats.list_chats import ListChatsUseCase
from src.application.use_cases.chat.start_chat.start_chat import StartChatUseCase
from src.dependencies.settings import ChatInfrastructureMode, get_settings
from src.infrastructure.llm.bedrock_knowledge_base_chat_client import (
    BedrockKnowledgeBaseChatClient,
)
from src.infrastructure.llm.simulated_chat_generation_client import (
    SimulatedChatGenerationClient,
)
from src.infrastructure.repositories.chat.dynamodb_chat_repository import (
    DynamoDbChatRepository,
)


@lru_cache
def get_chat_repository() -> DynamoDbChatRepository:
    settings = get_settings()
    client_options: dict[str, str] = {"region_name": settings.aws_region}
    if settings.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL:
        assert settings.dynamodb_endpoint_url is not None
        client_options["endpoint_url"] = settings.dynamodb_endpoint_url
    client = boto3.client("dynamodb", **client_options)
    return DynamoDbChatRepository(client, table_name=settings.dynamodb_chat_table_name)


@lru_cache
def get_list_chats_use_case() -> ListChatsProtocol:
    return ListChatsUseCase(get_chat_repository())


@lru_cache
def get_list_chat_messages_use_case() -> ListChatMessagesProtocol:
    return ListChatMessagesUseCase(get_chat_repository())


@lru_cache
def get_chat_generation_client() -> ChatGenerationClientProtocol:
    settings = get_settings()
    if settings.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL:
        return SimulatedChatGenerationClient(
            delay_seconds=settings.simulated_llm_delay_seconds
        )

    assert settings.bedrock_knowledge_base_id is not None
    assert settings.bedrock_model_arn is not None
    knowledge_base_client = boto3.client(
        "bedrock-agent-runtime", region_name=settings.aws_region
    )
    model_client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    generation_client = BedrockKnowledgeBaseChatClient(
        knowledge_base_client,
        model_client,
        knowledge_base_id=settings.bedrock_knowledge_base_id,
        model_arn=settings.bedrock_model_arn,
    )
    return generation_client


@lru_cache
def get_continue_chat_use_case() -> ContinueChatProtocol:
    repository = get_chat_repository()
    return ContinueChatUseCase(get_chat_generation_client(), repository)


@lru_cache
def get_start_chat_use_case() -> StartChatProtocol:
    return StartChatUseCase(get_chat_generation_client(), get_chat_repository())
