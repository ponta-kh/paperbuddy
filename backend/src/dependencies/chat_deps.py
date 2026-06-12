from functools import lru_cache

from src.application.ports.input.chat.continue_chat_protocol import ContinueChatProtocol
from src.application.ports.input.chat.delete_chat_protocol import DeleteChatProtocol
from src.application.ports.input.chat.list_chat_messages_protocol import (
    ListChatMessagesProtocol,
)
from src.application.ports.input.chat.list_chats_protocol import ListChatsProtocol
from src.application.ports.input.chat.rename_chat_protocol import RenameChatProtocol
from src.application.ports.input.chat.start_chat_protocol import (
    StartChatProtocol,
)
from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
)
from src.application.use_cases.chat.continue_chat.continue_chat import (
    ContinueChatUseCase,
)
from src.application.use_cases.chat.delete_chat.delete_chat import DeleteChatUseCase
from src.application.use_cases.chat.list_chat_messages.list_chat_messages import (
    ListChatMessagesUseCase,
)
from src.application.use_cases.chat.list_chats.list_chats import ListChatsUseCase
from src.application.use_cases.chat.rename_chat.rename_chat import RenameChatUseCase
from src.application.use_cases.chat.start_chat.start_chat import StartChatUseCase
from src.dependencies.client_factories import (
    create_chat_generation_client,
    create_dynamodb_client,
)
from src.dependencies.settings import get_settings
from src.infrastructure.repositories.chat.dynamodb_chat_repository import (
    DynamoDbChatRepository,
)


@lru_cache
def get_chat_repository() -> DynamoDbChatRepository:
    settings = get_settings()
    client = create_dynamodb_client(settings)
    return DynamoDbChatRepository(client, table_name=settings.dynamodb_chat_table_name)


@lru_cache
def get_list_chats_use_case() -> ListChatsProtocol:
    return ListChatsUseCase(get_chat_repository())


@lru_cache
def get_list_chat_messages_use_case() -> ListChatMessagesProtocol:
    return ListChatMessagesUseCase(get_chat_repository())


@lru_cache
def get_chat_generation_client() -> ChatGenerationClientProtocol:
    return create_chat_generation_client(get_settings())


@lru_cache
def get_continue_chat_use_case() -> ContinueChatProtocol:
    repository = get_chat_repository()
    return ContinueChatUseCase(get_chat_generation_client(), repository)


@lru_cache
def get_start_chat_use_case() -> StartChatProtocol:
    return StartChatUseCase(get_chat_generation_client(), get_chat_repository())


@lru_cache
def get_rename_chat_use_case() -> RenameChatProtocol:
    return RenameChatUseCase(get_chat_repository())


@lru_cache
def get_delete_chat_use_case() -> DeleteChatProtocol:
    return DeleteChatUseCase(get_chat_repository())
