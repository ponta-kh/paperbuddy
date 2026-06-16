from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.domain.exceptions.chat_exception import (
    ChatContinuationExpiredError,
    ChatOwnershipMismatchError,
    InvalidChatIdError,
    InvalidChatTurnError,
    InvalidMessageSenderError,
    InvalidSessionIdError,
    MessageSentAtOutOfOrderError,
)
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt


@dataclass(frozen=True, slots=True)
class ChatMessage:
    chat_id: UUID
    request_id: UUID
    sender: MessageSender
    content: Prompt | str
    sent_at: datetime

    def __post_init__(self) -> None:
        # ChatMessageは保存後に更新しない前提のため、
        # 生成時にターンID、発信者、内容の対応を確定する。
        if not isinstance(self.chat_id, UUID):
            raise InvalidChatIdError
        if not isinstance(self.request_id, UUID):
            raise InvalidChatTurnError
        if self.sent_at.tzinfo is None:
            raise ValueError("sent_at must be timezone-aware")
        if self.sender is MessageSender.USER and not isinstance(self.content, Prompt):
            raise InvalidMessageSenderError
        if self.sender is MessageSender.LLM and not isinstance(self.content, str):
            raise InvalidMessageSenderError


@dataclass(slots=True)
class Chat:
    _CONTINUATION_LIMIT = timedelta(hours=24)

    chat_id: UUID
    session_id: str
    title: str
    user_id: UUID
    created_at: datetime
    last_updated_at: datetime
    version: int

    @classmethod
    def create(
        cls,
        *,
        chat_id: UUID,
        session_id: str,
        title: str,
        user_id: UUID,
        answered_at: datetime,
    ) -> "Chat":
        if not isinstance(chat_id, UUID):
            raise InvalidChatIdError
        if not session_id.strip():
            raise InvalidSessionIdError
        if answered_at.tzinfo is None:
            raise ValueError("answered_at must be timezone-aware")
        # 初回回答日時を作成日時と最終更新日時の単一の基準にし、
        # 初期状態の時刻ずれを防ぐ。
        return cls(
            chat_id=chat_id,
            session_id=session_id,
            title=title,
            user_id=user_id,
            created_at=answered_at,
            last_updated_at=answered_at,
            version=0,
        )

    def validate_started_turn(
        self,
        *,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        self._validate_turn_pair(user_message=user_message, llm_message=llm_message)
        if user_message.sent_at > llm_message.sent_at:
            raise MessageSentAtOutOfOrderError
        if (
            llm_message.sent_at != self.created_at
            or llm_message.sent_at != self.last_updated_at
        ):
            raise MessageSentAtOutOfOrderError

    def record_exchange(
        self,
        *,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        self._validate_turn_pair(user_message=user_message, llm_message=llm_message)
        if user_message.sent_at < self.last_updated_at:
            raise MessageSentAtOutOfOrderError
        if llm_message.sent_at < user_message.sent_at:
            raise MessageSentAtOutOfOrderError
        # 保存前にDomain内で次バージョンへ進め、
        # Repositoryの楽観排他条件に使える状態にする。
        self.last_updated_at = llm_message.sent_at
        self.version += 1

    def ensure_continuable_at(self, requested_at: datetime) -> None:
        if requested_at.tzinfo is None:
            raise ValueError("requested_at must be timezone-aware")
        if requested_at - self.last_updated_at > self._CONTINUATION_LIMIT:
            raise ChatContinuationExpiredError

    def ensure_owned_by(self, user_id: UUID) -> None:
        if self.user_id != user_id:
            raise ChatOwnershipMismatchError

    def _validate_turn_pair(
        self,
        *,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        # 初回開始と継続会話で同じターン構成チェックを使い、
        # 検証条件のずれを避ける。
        if (
            user_message.chat_id != self.chat_id
            or llm_message.chat_id != self.chat_id
            or user_message.request_id != llm_message.request_id
            or user_message.sender is not MessageSender.USER
            or llm_message.sender is not MessageSender.LLM
        ):
            raise InvalidChatTurnError
