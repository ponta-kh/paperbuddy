from functools import lru_cache
from typing import Any

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
    DynamoDbChatCommandRepository,
    DynamoDbChatDeletionRepository,
    DynamoDbChatQueryRepository,
    DynamoDbChatTitleRepository,
)


@lru_cache
def get_chat_dynamodb_client() -> Any:
    """チャット用DynamoDBクライアントを返すDIファクトリ。"""

    return create_dynamodb_client(get_settings())


def _create_chat_repository(repository_type: type[Any]) -> Any:
    settings = get_settings()
    return repository_type(
        get_chat_dynamodb_client(),
        table_name=settings.dynamodb_chat_table_name,
    )


@lru_cache
def get_chat_command_repository() -> DynamoDbChatCommandRepository:
    """チャットCommand Repository実装を返すDIファクトリ。"""

    return _create_chat_repository(DynamoDbChatCommandRepository)


@lru_cache
def get_chat_query_repository() -> DynamoDbChatQueryRepository:
    """チャットQuery Repository実装を返すDIファクトリ。"""

    return _create_chat_repository(DynamoDbChatQueryRepository)


@lru_cache
def get_chat_title_repository() -> DynamoDbChatTitleRepository:
    """チャットタイトル更新Repository実装を返すDIファクトリ。"""

    return _create_chat_repository(DynamoDbChatTitleRepository)


@lru_cache
def get_chat_deletion_repository() -> DynamoDbChatDeletionRepository:
    """チャット削除Repository実装を返すDIファクトリ。"""

    return _create_chat_repository(DynamoDbChatDeletionRepository)


@lru_cache
def get_list_chats_use_case() -> ListChatsProtocol:
    """チャット一覧取得ユースケースを返すDIファクトリ。"""

    return ListChatsUseCase(get_chat_query_repository())


@lru_cache
def get_list_chat_messages_use_case() -> ListChatMessagesProtocol:
    """チャットメッセージ履歴取得ユースケースを返すDIファクトリ。"""

    return ListChatMessagesUseCase(get_chat_query_repository())


@lru_cache
def get_chat_generation_client() -> ChatGenerationClientProtocol:
    """設定に応じたLLM回答生成Clientを返すDIファクトリ。"""

    return create_chat_generation_client(get_settings())


@lru_cache
def get_continue_chat_use_case() -> ContinueChatProtocol:
    """チャット継続ユースケースを返すDIファクトリ。"""

    repository = get_chat_command_repository()
    return ContinueChatUseCase(get_chat_generation_client(), repository)


@lru_cache
def get_start_chat_use_case() -> StartChatProtocol:
    """チャット開始ユースケースを返すDIファクトリ。"""

    return StartChatUseCase(get_chat_generation_client(), get_chat_command_repository())


@lru_cache
def get_rename_chat_use_case() -> RenameChatProtocol:
    """チャットタイトル変更ユースケースを返すDIファクトリ。"""

    return RenameChatUseCase(get_chat_title_repository())


@lru_cache
def get_delete_chat_use_case() -> DeleteChatProtocol:
    """チャット削除ユースケースを返すDIファクトリ。"""

    return DeleteChatUseCase(get_chat_deletion_repository())
