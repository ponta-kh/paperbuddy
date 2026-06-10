from src.application.use_cases.chat.delete_chat.delete_chat_dto import DeleteChatInput
from src.domain.repositories.chat_deletion_repository_protocol import (
    ChatDeletionRepositoryProtocol,
)


class DeleteChatUseCase:
    def __init__(self, chat_repository: ChatDeletionRepositoryProtocol) -> None:
        self._chat_repository = chat_repository

    async def execute(self, command: DeleteChatInput) -> None:
        await self._chat_repository.delete_chat(chat_id=command.chat_id)
