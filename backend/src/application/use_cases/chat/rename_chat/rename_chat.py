import logging

from src.application.use_cases.chat.rename_chat.rename_chat_dto import (
    RenameChatInput,
    RenameChatOutput,
)
from src.domain.repositories.chat_title_repository_protocol import (
    ChatTitleRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class RenameChatUseCase:
    def __init__(self, chat_repository: ChatTitleRepositoryProtocol) -> None:
        self._chat_repository = chat_repository

    async def execute(self, command: RenameChatInput) -> RenameChatOutput:
        try:
            await self._chat_repository.update_title(
                chat_id=command.chat_id,
                user_id=command.user_id,
                title=command.title,
            )
        except Exception:
            logger.exception(
                "チャットタイトルの変更に失敗しました",
                extra={
                    "event": "rename_chat_failed",
                    "request_id": str(command.request_id),
                    "user_id": str(command.user_id),
                    "chat_id": str(command.chat_id),
                },
            )
            raise
        return RenameChatOutput(chat_id=command.chat_id, title=command.title)
