from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.domain.entities.chat.chat import ChatCitation


@dataclass(frozen=True, slots=True)
class ChatSummary:
    """チャット一覧表示用の読み取りモデル。"""

    chat_id: UUID
    title: str
    created_at: datetime
    last_updated_at: datetime


@dataclass(frozen=True, slots=True)
class ChatMessageRecord:
    """チャットメッセージ履歴表示用の読み取りモデル。"""

    request_id: UUID
    sender: str
    content: str
    sent_at: datetime
    citations: tuple[ChatCitation, ...] = ()


class ChatQueryRepositoryProtocol(Protocol):
    """チャット読み取り用Repository契約。"""

    async def list_chats_by_user_id(self, user_id: UUID) -> tuple[ChatSummary, ...]:
        """指定ユーザーに紐づくチャット一覧を取得する。

        Raises:
            RepositoryNotFoundError: 指定ユーザーのチャット一覧が存在しない場合。
            RepositoryAccessError: チャット一覧の取得に失敗した場合。
        """
        ...

    async def list_messages_by_chat_id(
        self,
        *,
        user_id: UUID,
        chat_id: UUID,
    ) -> tuple[ChatMessageRecord, ...]:
        """指定チャットのメッセージ履歴を取得する。

        Raises:
            RepositoryNotFoundError: 指定チャットが存在しない場合。
            RepositoryAccessError: メッセージ履歴の取得に失敗した場合。
        """
        ...
