from uuid import UUID

import pytest

from src.application.use_cases.chat.delete_chat.delete_chat import DeleteChatUseCase
from src.application.use_cases.chat.delete_chat.delete_chat_dto import DeleteChatInput

CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")


class StubChatRepository:
    def __init__(self) -> None:
        self.deleted_chat_id: UUID | None = None

    async def delete_chat(self, *, chat_id: UUID) -> None:
        self.deleted_chat_id = chat_id


@pytest.mark.asyncio
async def test_delete_chat_deletes_items_for_chat_id() -> None:
    repository = StubChatRepository()

    await DeleteChatUseCase(repository).execute(DeleteChatInput(chat_id=CHAT_ID))

    assert repository.deleted_chat_id == CHAT_ID
