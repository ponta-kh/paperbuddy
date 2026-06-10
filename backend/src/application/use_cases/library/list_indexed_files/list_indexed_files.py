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
        indexed_files = await self._indexed_file_catalog.list_indexed_files()
        return ListIndexedFilesOutput(
            files=tuple(
                IndexedFileOutput(name=indexed_file.name)
                for indexed_file in indexed_files
            )
        )
