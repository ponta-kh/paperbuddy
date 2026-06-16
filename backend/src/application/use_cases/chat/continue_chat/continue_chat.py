import logging
from collections.abc import Callable
from datetime import datetime, timezone

from src.application.exceptions import ChatContinuationExpiredError
from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
    ChatGenerationConfigurationError,
    ChatGenerationPermissionDeniedError,
    ChatGenerationRateLimitError,
    ChatGenerationSessionUnavailableError,
    ChatGenerationUnavailableError,
    ContinueGeneratedChatResult,
    InvalidChatGenerationResponseError,
)
from src.application.use_cases.chat.continue_chat.continue_chat_dto import (
    ContinueChatInput,
    ContinueChatOutput,
)
from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.exceptions.chat_exception import (
    ChatContinuationExpiredError as DomainChatContinuationExpiredError,
)
from src.domain.exceptions.chat_exception import (
    ChatOwnershipMismatchError,
)
from src.domain.repositories.chat_command_repository_protocol import (
    ChatCommandRepositoryProtocol,
    ChatNotFoundError,
)
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt

logger = logging.getLogger(__name__)


class ContinueChatUseCase:
    def __init__(
        self,
        chat_generation_client: ChatGenerationClientProtocol,
        chat_command_repository: ChatCommandRepositoryProtocol,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._chat_generation_client = chat_generation_client
        self._chat_command_repository = chat_command_repository
        self._now = now or (lambda: datetime.now(timezone.utc))

    async def execute(self, command: ContinueChatInput) -> ContinueChatOutput:
        prompt = Prompt(command.prompt)
        # チャットを取得してから所有者を確認し、
        # 権限外リクエストで副作用を起こさない。
        chat = await self._get_owned_chat(command)
        user_sent_at = self._now()
        # 会話継続期限はDomainルールとして外部生成前に判定し、
        # 期限切れのチャットで回答だけが生成される状態を避ける。
        try:
            chat.ensure_continuable_at(user_sent_at)
        except DomainChatContinuationExpiredError as error:
            logger.warning(
                "チャット継続期限切れのため処理を中断しました",
                extra={
                    "event": "continue_chat_expired",
                    "request_id": str(command.request_id),
                    "user_id": str(command.user_id),
                    "chat_id": str(command.chat_id),
                },
            )
            raise ChatContinuationExpiredError from error

        generated = await self._continue_chat_generation(
            command, chat.session_id, prompt.value
        )
        answered_at = self._now()
        user_message = ChatMessage(
            chat_id=chat.chat_id,
            request_id=command.request_id,
            sender=MessageSender.USER,
            content=prompt,
            sent_at=user_sent_at,
        )
        llm_message = ChatMessage(
            chat_id=chat.chat_id,
            request_id=command.request_id,
            sender=MessageSender.LLM,
            content=generated.answer,
            sent_at=answered_at,
        )
        # Domain側で発信順序と更新バージョンを確定してから、
        # Repository側の楽観排他保存へ渡す。
        chat.record_exchange(user_message=user_message, llm_message=llm_message)
        try:
            await self._chat_command_repository.save_exchange(
                chat, user_message, llm_message
            )
        except Exception:
            logger.exception(
                "継続チャットの保存に失敗しました",
                extra={
                    "event": "continue_chat_save_failed",
                    "request_id": str(command.request_id),
                    "user_id": str(command.user_id),
                    "chat_id": str(command.chat_id),
                },
            )
            raise
        return ContinueChatOutput(
            chat_id=chat.chat_id,
            answer=generated.answer,
            title=chat.title,
            last_updated_at=chat.last_updated_at,
        )

    async def _get_owned_chat(self, command: ContinueChatInput) -> Chat:
        try:
            chat = await self._chat_command_repository.get_chat(
                chat_id=command.chat_id,
            )
        except Exception:
            logger.exception(
                "継続対象チャットの取得に失敗しました",
                extra={
                    "event": "continue_chat_load_failed",
                    "request_id": str(command.request_id),
                    "user_id": str(command.user_id),
                    "chat_id": str(command.chat_id),
                },
            )
            raise

        try:
            chat.ensure_owned_by(command.user_id)
        except ChatOwnershipMismatchError as error:
            logger.warning(
                "継続対象チャットの所有者が一致しません",
                extra={
                    "event": "continue_chat_owner_mismatch",
                    "request_id": str(command.request_id),
                    "user_id": str(command.user_id),
                    "chat_id": str(command.chat_id),
                },
            )
            raise ChatNotFoundError from error

        return chat

    async def _continue_chat_generation(
        self, command: ContinueChatInput, session_id: str, prompt: str
    ) -> ContinueGeneratedChatResult:
        try:
            return await self._chat_generation_client.continue_chat(session_id, prompt)
        except ChatGenerationSessionUnavailableError as error:
            self._log_generation_error(
                "チャット生成サービス上のセッションを継続できません",
                event="continue_chat_generation_session_unavailable",
                command=command,
                level=logging.WARNING,
            )
            raise ChatContinuationExpiredError from error
        except ChatGenerationRateLimitError:
            self._log_generation_error(
                "チャット継続の回答生成がレート制限されました",
                event="continue_chat_generation_rate_limited",
                command=command,
                level=logging.WARNING,
            )
            raise
        except ChatGenerationPermissionDeniedError:
            self._log_generation_error(
                "チャット継続の回答生成で権限エラーが発生しました",
                event="continue_chat_generation_permission_denied",
                command=command,
            )
            raise
        except ChatGenerationConfigurationError:
            self._log_generation_error(
                "チャット継続の回答生成設定が不正です",
                event="continue_chat_generation_configuration_error",
                command=command,
            )
            raise
        except InvalidChatGenerationResponseError:
            self._log_generation_error(
                "チャット継続の回答生成レスポンスが不正です",
                event="continue_chat_generation_invalid_response",
                command=command,
                level=logging.WARNING,
            )
            raise
        except ChatGenerationUnavailableError:
            self._log_generation_error(
                "チャット継続の回答生成に失敗しました",
                event="continue_chat_generation_unavailable",
                command=command,
            )
            raise

    @staticmethod
    def _log_generation_error(
        message: str,
        *,
        event: str,
        command: ContinueChatInput,
        level: int = logging.ERROR,
    ) -> None:
        logger.log(
            level,
            message,
            extra={
                "event": event,
                "request_id": str(command.request_id),
                "user_id": str(command.user_id),
                "chat_id": str(command.chat_id),
            },
            exc_info=True,
        )
