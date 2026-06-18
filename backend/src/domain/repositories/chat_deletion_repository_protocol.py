from typing import Protocol
from uuid import UUID


class ChatDeleteError(Exception):
    """チャット削除に失敗した場合の例外。"""

    pass


class ChatDeletionRepositoryProtocol(Protocol):
    """チャット集約を削除するRepository契約。"""

    async def delete_chat(self, *, chat_id: UUID, user_id: UUID) -> None:
        """所有者に紐づくチャットを削除する。

        Args:
            chat_id: 削除対象のチャットID。
            user_id: 削除を要求したユーザーID。

        Raises:
            ChatDeleteError: チャット削除に失敗した場合。
        """
        ...
