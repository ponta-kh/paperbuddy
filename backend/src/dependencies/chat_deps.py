import os
from functools import lru_cache

import boto3

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
def get_start_chat_use_case() -> StartChatUseCase:
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
    return StartChatUseCase(generation_client, get_chat_repository())
