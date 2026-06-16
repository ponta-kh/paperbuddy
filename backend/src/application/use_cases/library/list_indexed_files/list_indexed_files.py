from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.indexed_file_catalog_protocol import (
    IndexedFileCatalogProtocol,
)
from src.application.use_cases.library.list_indexed_files.list_indexed_files_dto import (
    IndexedFileOutput,
    ListIndexedFilesOutput,
)


class ListIndexedFilesUseCase:
    def __init__(self, indexed_file_catalog: IndexedFileCatalogProtocol) -> None:
        self._indexed_file_catalog = indexed_file_catalog

    async def execute(self) -> ListIndexedFilesOutput:
        try:
            indexed_files = await self._indexed_file_catalog.list_indexed_files()
        except RepositoryNotFoundError:
            indexed_files = ()

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
