import logging

from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.chat import ChatQueryRepositoryProtocol
from src.application.use_cases.chat.list_chats.list_chats_dto import (
    ChatSummaryOutput,
    ListChatsInput,
    ListChatsOutput,
)

logger = logging.getLogger(__name__)


class ListChatsUseCase:
    """ユーザーに紐づくチャット一覧を取得するユースケース。"""

    def __init__(self, chat_repository: ChatQueryRepositoryProtocol) -> None:
        self._chat_repository = chat_repository

    async def execute(self, query: ListChatsInput) -> ListChatsOutput:
        """チャット一覧を取得し、存在しない場合は空一覧として返す。

        Raises:
            RepositoryAccessError: チャット一覧の取得に失敗した場合。
        """

        try:
            chats = await self._chat_repository.list_chats_by_user_id(query.user_id)
        except RepositoryNotFoundError:
            logger.warning(
                "チャット一覧が見つからなかったため空一覧を返します",
                extra={
                    "event": "list_chats_not_found",
                    "request_id": str(query.request_id),
                    "user_id": str(query.user_id),
                },
            )
            # 一覧取得では対象なしを正常な空一覧として扱い、
            # 呼び出し元に削除済み状態を意識させない。
            return ListChatsOutput(chats=())
        except Exception:
            logger.exception(
                "チャット一覧の取得に失敗しました",
                extra={
                    "event": "list_chats_failed",
                    "request_id": str(query.request_id),
                    "user_id": str(query.user_id),
                },
            )
            raise

        return ListChatsOutput(
            chats=tuple(
                ChatSummaryOutput(
                    chat_id=chat.chat_id,
                    title=chat.title,
                    created_at=chat.created_at,
                    last_updated_at=chat.last_updated_at,
                )
                for chat in chats
            )
        )
