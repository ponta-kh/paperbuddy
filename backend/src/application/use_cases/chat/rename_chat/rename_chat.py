from src.application.use_cases.chat.rename_chat.rename_chat_dto import (
    RenameChatInput,
    RenameChatOutput,
)
from src.domain.repositories.chat_title_repository_protocol import (
    ChatTitleRepositoryProtocol,
)


class RenameChatUseCase:
    def __init__(self, chat_repository: ChatTitleRepositoryProtocol) -> None:
        self._chat_repository = chat_repository

    async def execute(self, command: RenameChatInput) -> RenameChatOutput:
        await self._chat_repository.update_title(
            chat_id=command.chat_id,
            user_id=command.user_id,
            title=command.title,
        )
        return RenameChatOutput(chat_id=command.chat_id, title=command.title)
