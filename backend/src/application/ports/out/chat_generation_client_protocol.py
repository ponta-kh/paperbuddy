from dataclasses import dataclass
from typing import Protocol, TypeAlias

from src.domain.entities.chat.chat import ChatCitation, ChatCitationSource


class ChatGenerationError(Exception):
    """LLM回答生成で発生する例外の基底クラス。"""

    pass


class ChatGenerationUnavailableError(ChatGenerationError):
    """LLM回答生成サービスが一時的に利用できない場合の例外。"""

    pass


class ChatGenerationRateLimitError(ChatGenerationUnavailableError):
    """LLM回答生成サービスでレート制限された場合の例外。"""

    pass


class ChatGenerationPermissionDeniedError(ChatGenerationError):
    """LLM回答生成サービスへの権限が不足している場合の例外。"""

    pass


class ChatGenerationConfigurationError(ChatGenerationError):
    """LLM回答生成に必要な設定が不正な場合の例外。"""

    pass


class ChatGenerationSessionUnavailableError(ChatGenerationError):
    """LLM回答生成サービス上の継続セッションが利用できない場合の例外。"""

    pass


class InvalidChatGenerationResponseError(ChatGenerationError):
    """LLM回答生成レスポンスが期待形式ではない場合の例外。"""

    pass


GeneratedChatCitationSource: TypeAlias = ChatCitationSource
GeneratedChatCitation: TypeAlias = ChatCitation


@dataclass(frozen=True, slots=True)
class StartGeneratedChatResult:
    """新規チャットのLLM回答生成結果。"""

    session_id: str
    answer: str
    citations: tuple[GeneratedChatCitation, ...] = ()


@dataclass(frozen=True, slots=True)
class ContinueGeneratedChatResult:
    """継続チャットのLLM回答生成結果。"""

    session_id: str
    answer: str
    citations: tuple[GeneratedChatCitation, ...] = ()


class ChatGenerationClientProtocol(Protocol):
    """LLM回答生成を行う出力ポート。"""

    async def start_chat(self, prompt: str) -> StartGeneratedChatResult:
        """新規チャット用の回答、セッションID、引用情報を生成する。

        Raises:
            ChatGenerationRateLimitError: LLM回答生成サービスでレート制限された場合。
            ChatGenerationPermissionDeniedError: LLM回答生成サービスへの権限が不足している場合。
            ChatGenerationConfigurationError: LLM回答生成に必要な設定が不正な場合。
            ChatGenerationUnavailableError: LLM回答生成サービスが一時的に利用できない場合。
            InvalidChatGenerationResponseError: LLM回答生成レスポンスが期待形式ではない場合。
        """
        ...

    async def continue_chat(
        self, session_id: str, prompt: str
    ) -> ContinueGeneratedChatResult:
        """既存セッションを使って継続チャット用の回答と引用情報を生成する。

        Raises:
            ChatGenerationSessionUnavailableError: 指定セッションを継続できない場合。
            ChatGenerationRateLimitError: LLM回答生成サービスでレート制限された場合。
            ChatGenerationPermissionDeniedError: LLM回答生成サービスへの権限が不足している場合。
            ChatGenerationConfigurationError: LLM回答生成に必要な設定が不正な場合。
            ChatGenerationUnavailableError: LLM回答生成サービスが一時的に利用できない場合。
            InvalidChatGenerationResponseError: LLM回答生成レスポンスが期待形式ではない場合。
        """
        ...
