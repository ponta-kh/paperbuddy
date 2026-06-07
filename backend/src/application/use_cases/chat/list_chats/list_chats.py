from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.chat import ChatQueryRepositoryProtocol
from src.application.use_cases.chat.list_chats.list_chats_dto import (
    ChatSummaryOutput,
    ListChatsInput,
    ListChatsOutput,
)


class ListChatsUseCase:
    def __init__(self, chat_repository: ChatQueryRepositoryProtocol) -> None:
        self._chat_repository = chat_repository

    async def execute(self, query: ListChatsInput) -> ListChatsOutput:
        try:
            chats = await self._chat_repository.list_chats_by_user_id(query.user_id)
        except RepositoryNotFoundError:
            return ListChatsOutput(chats=())

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
