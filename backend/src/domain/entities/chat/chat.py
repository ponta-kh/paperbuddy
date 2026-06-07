from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.exceptions.chat_exception import (
    InvalidChatIdError,
    InvalidChatTurnError,
    InvalidMessageSenderError,
    MessageSentAtOutOfOrderError,
)
from src.domain.value_objects.chat.chat_turn_id import ChatTurnId
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt


@dataclass(frozen=True, slots=True)
class ChatMessage:
    chat_id: str
    turn_id: ChatTurnId
    sender: MessageSender
    content: Prompt | str
    sent_at: datetime

    def __post_init__(self) -> None:
        if not self.chat_id.strip():
            raise InvalidChatIdError
        if self.sent_at.tzinfo is None:
            raise ValueError("sent_at must be timezone-aware")
        if self.sender is MessageSender.USER and not isinstance(self.content, Prompt):
            raise InvalidMessageSenderError
        if self.sender is MessageSender.LLM and not isinstance(self.content, str):
            raise InvalidMessageSenderError


@dataclass(slots=True)
class Chat:
    chat_id: str
    title: str
    user_id: UUID
    created_at: datetime
    last_updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        chat_id: str,
        title: str,
        user_id: UUID,
        answered_at: datetime,
    ) -> "Chat":
        if not chat_id.strip():
            raise InvalidChatIdError
        if answered_at.tzinfo is None:
            raise ValueError("answered_at must be timezone-aware")
        return cls(
            chat_id=chat_id,
            title=title,
            user_id=user_id,
            created_at=answered_at,
            last_updated_at=answered_at,
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
        self.last_updated_at = llm_message.sent_at

    def _validate_turn_pair(
        self,
        *,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        if (
            user_message.chat_id != self.chat_id
            or llm_message.chat_id != self.chat_id
            or user_message.turn_id != llm_message.turn_id
            or user_message.sender is not MessageSender.USER
            or llm_message.sender is not MessageSender.LLM
        ):
            raise InvalidChatTurnError
