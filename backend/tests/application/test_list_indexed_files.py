import logging
from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.application.exceptions import RepositoryNotFoundError
from src.application.ports.out.indexed_file_catalog_protocol import IndexedFile
from src.application.use_cases.library.list_indexed_files.list_indexed_files import (
    ListIndexedFilesUseCase,
)
from src.application.use_cases.library.list_indexed_files.list_indexed_files_dto import (
    ListIndexedFilesInput,
)

REQUEST_ID = UUID("019ecde4-0000-7000-8000-000000000001")


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


class FailingIndexedFileCatalog:
    async def list_indexed_files(self) -> tuple[IndexedFile, ...]:
        raise RuntimeError("DynamoDB failure")


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

    output = await ListIndexedFilesUseCase(catalog).execute(
        ListIndexedFilesInput(request_id=REQUEST_ID)
    )

    assert catalog.called
    assert tuple(file.name for file in output.files) == (
        "paper-a.pdf",
        "paper-b.pdf",
    )
    assert tuple(file.category for file in output.files) == ("LLM", "経済")


@pytest.mark.asyncio
async def test_list_indexed_files_returns_empty_list() -> None:
    output = await ListIndexedFilesUseCase(StubNotFoundIndexedFileCatalog()).execute(
        ListIndexedFilesInput(request_id=REQUEST_ID)
    )

    assert output.files == ()


@pytest.mark.asyncio
async def test_list_indexed_files_logs_not_found(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(
        logging.WARNING,
        logger=(
            "src.application.use_cases.library.list_indexed_files.list_indexed_files"
        ),
    ):
        output = await ListIndexedFilesUseCase(
            StubNotFoundIndexedFileCatalog()
        ).execute(ListIndexedFilesInput(request_id=REQUEST_ID))

    assert output.files == ()
    record = caplog.records[0]
    assert getattr(record, "event") == "list_indexed_files_not_found"
    assert getattr(record, "request_id") == str(REQUEST_ID)


@pytest.mark.asyncio
async def test_list_indexed_files_logs_repository_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with (
        caplog.at_level(
            logging.ERROR,
            logger=(
                "src.application.use_cases.library.list_indexed_files."
                "list_indexed_files"
            ),
        ),
        pytest.raises(RuntimeError, match="DynamoDB failure"),
    ):
        await ListIndexedFilesUseCase(FailingIndexedFileCatalog()).execute(
            ListIndexedFilesInput(request_id=REQUEST_ID)
        )

    record = caplog.records[0]
    assert getattr(record, "event") == "list_indexed_files_failed"
    assert getattr(record, "request_id") == str(REQUEST_ID)
