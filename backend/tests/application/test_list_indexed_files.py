from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.application.exceptions import RepositoryNotFoundError
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


class StubNotFoundIndexedFileCatalog:
    async def list_indexed_files(self) -> tuple[IndexedFile, ...]:
        raise RepositoryNotFoundError


@pytest.mark.asyncio
async def test_list_indexed_files_returns_catalog_results() -> None:
    catalog = StubIndexedFileCatalog(
        (
            IndexedFile(
                source_id=UUID("00000000-0000-0000-0000-000000000002"),
                s3_key="papers/b.pdf",
                name="paper-b.pdf",
                category="経済",
                status="indexed",
                s3_uploaded_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                rag_indexed_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
            ),
            IndexedFile(
                source_id=UUID("00000000-0000-0000-0000-000000000001"),
                s3_key="papers/a.pdf",
                name="paper-a.pdf",
                category="LLM",
                status="indexed",
                s3_uploaded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                rag_indexed_at=None,
            ),
        )
    )

    output = await ListIndexedFilesUseCase(catalog).execute()

    assert catalog.called
    assert tuple(file.name for file in output.files) == (
        "paper-a.pdf",
        "paper-b.pdf",
    )
    assert tuple(file.category for file in output.files) == ("LLM", "経済")


@pytest.mark.asyncio
async def test_list_indexed_files_returns_empty_list() -> None:
    output = await ListIndexedFilesUseCase(StubNotFoundIndexedFileCatalog()).execute()

    assert output.files == ()
