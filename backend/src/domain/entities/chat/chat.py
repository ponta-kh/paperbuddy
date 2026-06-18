from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.domain.exceptions.chat_exception import (
    ChatContinuationExpiredError,
    ChatOwnershipMismatchError,
    InvalidChatCitationError,
    InvalidChatIdError,
    InvalidChatTurnError,
    InvalidMessageSenderError,
    InvalidSessionIdError,
    MessageSentAtOutOfOrderError,
)
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt


@dataclass(frozen=True, slots=True)
class ChatCitationSource:
    """LLM回答の引用元を表すValue Object。

    引用元の抜粋本文、場所種別、URI、メタデータを保持する。
    """

    content: str
    location_type: str | None
    uri: str | None
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise InvalidChatCitationError
        if self.location_type is not None and not isinstance(self.location_type, str):
            raise InvalidChatCitationError
        if self.uri is not None and not isinstance(self.uri, str):
            raise InvalidChatCitationError
        if not isinstance(self.metadata, dict):
            raise InvalidChatCitationError


@dataclass(frozen=True, slots=True)
class ChatCitation:
    """LLM回答本文の引用箇所と参照元を表すValue Object。

    回答本文中の該当テキスト、文字位置、引用元一覧を保持する。
    """

    text: str
    span_start: int | None
    span_end: int | None
    sources: tuple[ChatCitationSource, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise InvalidChatCitationError
        if self.span_start is not None and not isinstance(self.span_start, int):
            raise InvalidChatCitationError
        if self.span_end is not None and not isinstance(self.span_end, int):
            raise InvalidChatCitationError
        if not isinstance(self.sources, tuple) or not all(
            isinstance(source, ChatCitationSource) for source in self.sources
        ):
            raise InvalidChatCitationError


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """チャット内の1メッセージを表すEntity。

    ユーザー発信メッセージはPromptを保持し、LLM発信メッセージは回答文字列を保持する。
    ユーザー発信メッセージは引用情報を持たない。
    """

    chat_id: UUID
    request_id: UUID
    sender: MessageSender
    content: Prompt | str
    sent_at: datetime
    citations: tuple[ChatCitation, ...] = ()

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
        if not isinstance(self.citations, tuple) or not all(
            isinstance(citation, ChatCitation) for citation in self.citations
        ):
            raise InvalidChatCitationError
        if self.sender is MessageSender.USER and self.citations:
            raise InvalidChatCitationError


@dataclass(slots=True)
class Chat:
    """ユーザーに紐づくチャットを表すAggregate Root。

    チャットの所有者、Bedrockセッション、最終更新時刻、楽観排他用バージョンを管理する。
    """

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
        """初回LLM回答を基準に新しいチャットを生成する。

        Args:
            chat_id: 生成するチャットの識別子。
            session_id: LLM側の会話継続用セッションID。
            title: チャット一覧に表示するタイトル。
            user_id: チャットを所有するユーザーID。
            answered_at: 初回LLM回答が生成された日時。

        Returns:
            初期状態のチャットAggregate。

        Raises:
            InvalidChatIdError: チャットIDがUUIDではない場合。
            InvalidSessionIdError: セッションIDが空の場合。
        """

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
        """チャット開始時のユーザー質問とLLM回答の整合性を検証する。

        Args:
            user_message: 初回ターンのユーザー発信メッセージ。
            llm_message: 初回ターンのLLM発信メッセージ。

        Raises:
            InvalidChatTurnError: メッセージのチャットID、リクエストID、発信者の対応が不正な場合。
            MessageSentAtOutOfOrderError: 初回ターンの送信時刻がチャット作成時刻と整合しない場合。
        """

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
        """継続ターンのユーザー質問とLLM回答をチャット状態へ反映する。

        Args:
            user_message: 継続ターンのユーザー発信メッセージ。
            llm_message: 継続ターンのLLM発信メッセージ。

        Raises:
            InvalidChatTurnError: メッセージのチャットID、リクエストID、発信者の対応が不正な場合。
            MessageSentAtOutOfOrderError: 継続ターンの送信時刻が既存チャット時刻と整合しない場合。
        """

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
        """指定日時にチャットを継続できることを確認する。

        Args:
            requested_at: 継続要求を受け付けた日時。

        Raises:
            ChatContinuationExpiredError: 最終更新から継続可能期間を超過している場合。
        """

        if requested_at.tzinfo is None:
            raise ValueError("requested_at must be timezone-aware")
        if requested_at - self.last_updated_at > self._CONTINUATION_LIMIT:
            raise ChatContinuationExpiredError

    def ensure_owned_by(self, user_id: UUID) -> None:
        """指定ユーザーがチャット所有者であることを確認する。

        Args:
            user_id: 操作を要求したユーザーID。

        Raises:
            ChatOwnershipMismatchError: 指定ユーザーがチャット所有者ではない場合。
        """

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
