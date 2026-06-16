from typing import Protocol

from src.application.use_cases.library.list_indexed_files.list_indexed_files_dto import (
    ListIndexedFilesInput,
    ListIndexedFilesOutput,
)


class ListIndexedFilesProtocol(Protocol):
    async def execute(self, query: ListIndexedFilesInput) -> ListIndexedFilesOutput: ...
