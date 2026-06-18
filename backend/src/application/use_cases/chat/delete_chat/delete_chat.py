import logging

from src.application.use_cases.chat.delete_chat.delete_chat_dto import DeleteChatInput
from src.domain.repositories.chat_deletion_repository_protocol import (
    ChatDeletionRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class DeleteChatUseCase:
    """ユーザーに紐づくチャットを削除するユースケース。"""

    def __init__(self, chat_repository: ChatDeletionRepositoryProtocol) -> None:
        self._chat_repository = chat_repository

    async def execute(self, command: DeleteChatInput) -> None:
        """指定ユーザーが所有するチャットを削除する。

        Raises:
            ChatDeleteError: チャット削除に失敗した場合。
        """

        try:
            await self._chat_repository.delete_chat(
                chat_id=command.chat_id,
                user_id=command.user_id,
            )
        except Exception:
            logger.exception(
                "チャット削除に失敗しました",
                extra={
                    "event": "delete_chat_failed",
                    "request_id": str(command.request_id),
                    "user_id": str(command.user_id),
                    "chat_id": str(command.chat_id),
                },
            )
            raise
