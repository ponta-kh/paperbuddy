from typing import Protocol

from src.application.use_cases.library.list_indexed_files.list_indexed_files_dto import (
    ListIndexedFilesInput,
    ListIndexedFilesOutput,
)


class ListIndexedFilesProtocol(Protocol):
    """インデックス済みファイル一覧取得ユースケースの入力ポート。"""

    async def execute(self, query: ListIndexedFilesInput) -> ListIndexedFilesOutput:
        """RAG検索対象として登録済みのファイル一覧を返す。"""
        ...
