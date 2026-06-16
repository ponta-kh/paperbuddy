import logging

from src.application.ports.out.chat import ChatQueryRepositoryProtocol
from src.application.use_cases.chat.list_chat_messages.list_chat_messages_dto import (
    ChatMessageOutput,
    ListChatMessagesInput,
    ListChatMessagesOutput,
)

logger = logging.getLogger(__name__)


class ListChatMessagesUseCase:
    def __init__(self, chat_repository: ChatQueryRepositoryProtocol) -> None:
        self._chat_repository = chat_repository

    async def execute(self, query: ListChatMessagesInput) -> ListChatMessagesOutput:
        try:
            messages = await self._chat_repository.list_messages_by_chat_id(
                user_id=query.user_id,
                chat_id=query.chat_id,
            )
        except Exception:
            logger.exception(
                "チャットメッセージ一覧の取得に失敗しました",
                extra={
                    "event": "list_chat_messages_failed",
                    "request_id": str(query.request_id),
                    "user_id": str(query.user_id),
                    "chat_id": str(query.chat_id),
                },
            )
            raise
        return ListChatMessagesOutput(
            chat_id=query.chat_id,
            messages=tuple(
                ChatMessageOutput(
                    request_id=message.request_id,
                    sender=message.sender,
                    content=message.content,
                    sent_at=message.sent_at,
                )
                for message in messages
            ),
        )
