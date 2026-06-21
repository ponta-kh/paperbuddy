import logging

from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.library.indexed_file_query_repository_protocol import (
    IndexedFileQueryRepositoryProtocol,
)
from src.application.use_cases.library.list_indexed_files.list_indexed_files_dto import (
    IndexedFileOutput,
    ListIndexedFilesInput,
    ListIndexedFilesOutput,
)

logger = logging.getLogger(__name__)


class ListIndexedFilesUseCase:
    """RAG検索対象として登録済みの論文一覧を取得するユースケース。"""

    def __init__(
        self, indexed_file_query_repository: IndexedFileQueryRepositoryProtocol
    ) -> None:
        self._indexed_file_query_repository = indexed_file_query_repository

    async def execute(self, query: ListIndexedFilesInput) -> ListIndexedFilesOutput:
        """インデックス済みファイル一覧をカテゴリ名と論文名の昇順で返す。

        Raises:
            RepositoryAccessError: ファイル一覧の取得に失敗した場合。
        """

        try:
            indexed_files = (
                await self._indexed_file_query_repository.list_indexed_files()
            )
        except RepositoryNotFoundError:
            logger.warning(
                "インデックス済みファイル一覧が見つからなかったため空一覧を返します",
                extra={
                    "event": "list_indexed_files_not_found",
                    "request_id": str(query.request_id),
                },
            )
            indexed_files = ()
        except Exception:
            logger.exception(
                "インデックス済みファイル一覧の取得に失敗しました",
                extra={
                    "event": "list_indexed_files_failed",
                    "request_id": str(query.request_id),
                },
            )
            raise

        # 表示順はユースケースで固定し、
        # 取得元の格納順や実装差に依存しない出力にする。
        sorted_files = sorted(
            indexed_files,
            key=lambda indexed_file: (indexed_file.category, indexed_file.name),
        )

        return ListIndexedFilesOutput(
            files=tuple(
                IndexedFileOutput(
                    source_id=indexed_file.source_id,
                    s3_key=indexed_file.s3_key,
                    name=indexed_file.name,
                    category=indexed_file.category,
                    status=indexed_file.status,
                    s3_uploaded_at=indexed_file.s3_uploaded_at,
                    rag_indexed_at=indexed_file.rag_indexed_at,
                )
                for indexed_file in sorted_files
            )
        )
