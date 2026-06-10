import pytest

from src.application.ports.out.indexed_file_catalog_protocol import IndexedFile
from src.application.use_cases.library.list_indexed_files.list_indexed_files import (
    ListIndexedFilesUseCase,
)


class StubIndexedFileCatalog:
    def __init__(self, files: tuple[IndexedFile, ...]) -> None:
        self.files = files
        self.called = False

    async def list_indexed_files(self) -> tuple[IndexedFile, ...]:
        self.called = True
        return self.files


@pytest.mark.asyncio
async def test_list_indexed_files_returns_catalog_results() -> None:
    catalog = StubIndexedFileCatalog(
        (IndexedFile(name="paper-a.pdf"), IndexedFile(name="paper-b.pdf"))
    )

    output = await ListIndexedFilesUseCase(catalog).execute()

    assert catalog.called
    assert tuple(file.name for file in output.files) == (
        "paper-a.pdf",
        "paper-b.pdf",
    )


@pytest.mark.asyncio
async def test_list_indexed_files_returns_empty_list() -> None:
    output = await ListIndexedFilesUseCase(StubIndexedFileCatalog(())).execute()

    assert output.files == ()
