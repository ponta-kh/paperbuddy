from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class IndexedFile:
    """RAG検索対象として登録済みのファイル読み取りモデル。"""

    source_id: UUID
    s3_key: str
    name: str
    category: str
    status: str
    s3_uploaded_at: datetime
    rag_indexed_at: datetime | None


class IndexedFileQueryRepositoryProtocol(Protocol):
    """インデックス済みファイル一覧を取得する出力ポート。"""

    async def list_indexed_files(self) -> tuple[IndexedFile, ...]:
        """RAG検索対象として登録済みのファイル一覧を取得する。

        Raises:
            RepositoryNotFoundError: 登録済みファイルが存在しない場合。
            RepositoryAccessError: ファイル一覧の取得に失敗した場合。
        """
        ...
