import os
from functools import lru_cache

import boto3

from src.application.ports.input.chat.list_chat_messages_protocol import (
    ListChatMessagesProtocol,
)
from src.application.ports.input.chat.continue_chat_protocol import ContinueChatProtocol
from src.application.ports.input.chat.list_chats_protocol import ListChatsProtocol
from src.application.ports.input.chat.start_chat_protocol import (
    StartChatProtocol,
)
from src.application.use_cases.chat.list_chat_messages.list_chat_messages import (
    ListChatMessagesUseCase,
)
from src.application.use_cases.chat.continue_chat.continue_chat import (
    ContinueChatUseCase,
)
from src.application.use_cases.chat.list_chats.list_chats import ListChatsUseCase
from src.application.use_cases.chat.start_chat.start_chat import StartChatUseCase
from src.infrastructure.llm.bedrock_knowledge_base_chat_client import (
    BedrockKnowledgeBaseChatClient,
)
from src.infrastructure.repositories.chat.in_memory_chat_repository import (
    InMemoryChatRepository,
)


@lru_cache
def get_chat_repository() -> InMemoryChatRepository:
    return InMemoryChatRepository()


@lru_cache
def get_list_chats_use_case() -> ListChatsProtocol:
    return ListChatsUseCase(get_chat_repository())


@lru_cache
def get_list_chat_messages_use_case() -> ListChatMessagesProtocol:
    return ListChatMessagesUseCase(get_chat_repository())


@lru_cache
def get_chat_generation_client() -> BedrockKnowledgeBaseChatClient:
    region = os.environ["AWS_REGION"]
    knowledge_base_id = os.environ["BEDROCK_KNOWLEDGE_BASE_ID"]
    model_arn = os.environ["BEDROCK_MODEL_ARN"]
    knowledge_base_client = boto3.client("bedrock-agent-runtime", region_name=region)
    model_client = boto3.client("bedrock-runtime", region_name=region)
    generation_client = BedrockKnowledgeBaseChatClient(
        knowledge_base_client,
        model_client,
        knowledge_base_id=knowledge_base_id,
        model_arn=model_arn,
    )
    return generation_client


@lru_cache
def get_continue_chat_use_case() -> ContinueChatProtocol:
    repository = get_chat_repository()
    return ContinueChatUseCase(get_chat_generation_client(), repository, repository)


@lru_cache
def get_start_chat_use_case() -> StartChatProtocol:
    return StartChatUseCase(get_chat_generation_client(), get_chat_repository())
