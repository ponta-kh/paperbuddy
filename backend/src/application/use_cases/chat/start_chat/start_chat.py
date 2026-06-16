import logging
from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID, uuid7

from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
    ChatGenerationConfigurationError,
    ChatGenerationPermissionDeniedError,
    ChatGenerationRateLimitError,
    ChatGenerationUnavailableError,
    InvalidChatGenerationResponseError,
    StartGeneratedChatResult,
)
from src.application.use_cases.chat.start_chat.start_chat_dto import (
    StartChatInput,
    StartChatOutput,
)
from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.repositories.chat_command_repository_protocol import (
    ChatCommandRepositoryProtocol,
)
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt

logger = logging.getLogger(__name__)


class StartChatUseCase:
    def __init__(
        self,
        chat_generation_client: ChatGenerationClientProtocol,
        chat_repository: ChatCommandRepositoryProtocol,
        now: Callable[[], datetime] | None = None,
        generate_chat_id: Callable[[], UUID] | None = None,
    ) -> None:
        self._chat_generation_client = chat_generation_client
        self._chat_repository = chat_repository
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._generate_chat_id = generate_chat_id or uuid7

    async def execute(self, command: StartChatInput) -> StartChatOutput:
        prompt = Prompt(command.prompt)
        # 外部生成前の時刻をユーザー発信日時として固定し、
        # 生成待ち時間で発信順序が崩れないようにする。
        user_sent_at = self._now()

        generated = await self._start_chat_generation(command, prompt.value)
        # 正常応答を受け取った時点をLLM回答日時とし、
        # チャット本体の作成・更新日時にも使う。
        answered_at = self._now()

        chat = Chat.create(
            chat_id=self._generate_chat_id(),
            session_id=generated.session_id,
            title=generated.title,
            user_id=command.user_id,
            answered_at=answered_at,
        )
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
        # 保存前にDomainルールを通し、
        # 永続化層へ不整合な初回ターンを渡さない。
        chat.validate_started_turn(user_message=user_message, llm_message=llm_message)

        try:
            await self._chat_repository.save_started_chat(
                chat, user_message, llm_message
            )
        except Exception:
            logger.exception(
                "開始したチャットの保存に失敗しました",
                extra={
                    "event": "start_chat_save_failed",
                    "request_id": str(command.request_id),
                    "user_id": str(command.user_id),
                    "chat_id": str(chat.chat_id),
                },
            )
            raise
        return StartChatOutput(
            chat_id=chat.chat_id,
            answer=generated.answer,
            title=generated.title,
            last_updated_at=chat.last_updated_at,
        )

    async def _start_chat_generation(
        self, command: StartChatInput, prompt: str
    ) -> StartGeneratedChatResult:
        try:
            return await self._chat_generation_client.start_chat(prompt)
        except ChatGenerationRateLimitError:
            self._log_generation_error(
                "チャット開始の回答生成がレート制限されました",
                event="start_chat_generation_rate_limited",
                command=command,
                level=logging.WARNING,
            )
            raise
        except ChatGenerationPermissionDeniedError:
            self._log_generation_error(
                "チャット開始の回答生成で権限エラーが発生しました",
                event="start_chat_generation_permission_denied",
                command=command,
            )
            raise
        except ChatGenerationConfigurationError:
            self._log_generation_error(
                "チャット開始の回答生成設定が不正です",
                event="start_chat_generation_configuration_error",
                command=command,
            )
            raise
        except InvalidChatGenerationResponseError:
            self._log_generation_error(
                "チャット開始の回答生成レスポンスが不正です",
                event="start_chat_generation_invalid_response",
                command=command,
                level=logging.WARNING,
            )
            raise
        except ChatGenerationUnavailableError:
            self._log_generation_error(
                "チャット開始の回答生成に失敗しました",
                event="start_chat_generation_unavailable",
                command=command,
            )
            raise

    @staticmethod
    def _log_generation_error(
        message: str,
        *,
        event: str,
        command: StartChatInput,
        level: int = logging.ERROR,
    ) -> None:
        logger.log(
            level,
            message,
            extra={
                "event": event,
                "request_id": str(command.request_id),
                "user_id": str(command.user_id),
            },
            exc_info=True,
        )
