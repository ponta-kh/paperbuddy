from typing import Protocol
from uuid import UUID

from src.domain.entities.chat.chat import Chat, ChatMessage


class ChatSaveError(Exception):
    """チャット集約の保存に失敗した場合の例外。"""

    pass


class ChatLoadError(Exception):
    """チャット集約の読み込みに失敗した場合の例外。"""

    pass


class ChatConflictError(Exception):
    """チャット集約の保存時に楽観排他競合が発生した場合の例外。"""

    pass


class ChatNotFoundError(Exception):
    """指定されたチャット集約が存在しない場合の例外。"""

    pass


class ChatCommandRepositoryProtocol(Protocol):
    """チャット集約を永続化するCommand Repository契約。"""

    async def get_chat(
        self,
        *,
        chat_id: UUID,
    ) -> Chat:
        """チャット集約を取得する。

        Args:
            chat_id: 取得対象のチャットID。

        Returns:
            取得したチャット集約。

        Raises:
            ChatNotFoundError: 指定されたチャットが存在しない場合。
            ChatLoadError: チャット集約の読み込みに失敗した場合。
        """
        ...

    async def save_started_chat(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        """開始済みチャットと初回ターンのメッセージを保存する。

        Args:
            chat: 保存対象のチャット集約。
            user_message: 初回ターンのユーザー発信メッセージ。
            llm_message: 初回ターンのLLM発信メッセージ。

        Raises:
            ChatConflictError: 同じチャットIDの保存済みデータと競合した場合。
            ChatSaveError: チャット集約の保存に失敗した場合。
        """
        ...

    async def save_exchange(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        """継続ターンのメッセージと更新後チャット集約を保存する。

        Args:
            chat: 更新後のチャット集約。
            user_message: 継続ターンのユーザー発信メッセージ。
            llm_message: 継続ターンのLLM発信メッセージ。

        Raises:
            ChatConflictError: 保存済みチャットのバージョンと競合した場合。
            ChatSaveError: チャット集約の保存に失敗した場合。
        """
        ...
