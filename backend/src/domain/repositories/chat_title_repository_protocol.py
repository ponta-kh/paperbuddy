from typing import Protocol
from uuid import UUID


class ChatTitleUpdateError(Exception):
    """チャットタイトル更新に失敗した場合の例外。"""

    pass


class ChatTitleRepositoryProtocol(Protocol):
    """チャットタイトルを更新するRepository契約。"""

    async def update_title(
        self,
        *,
        chat_id: UUID,
        user_id: UUID,
        title: str,
    ) -> None:
        """所有者に紐づくチャットのタイトルを更新する。

        Args:
            chat_id: 更新対象のチャットID。
            user_id: 更新を要求したユーザーID。
            title: 更新後のタイトル。

        Raises:
            ChatTitleUpdateError: チャットタイトル更新に失敗した場合。
        """
        ...
