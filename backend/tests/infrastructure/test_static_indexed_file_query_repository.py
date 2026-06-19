from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.application.ports.out.library.indexed_file_query_repository_protocol import (
    IndexedFile,
)
from src.infrastructure.repositories.library.static_indexed_file_query_repository import (
    StaticIndexedFileQueryRepository,
)


@pytest.mark.asyncio
async def test_static_indexed_file_query_repository_returns_configured_files() -> None:
    files = (
        IndexedFile(
            source_id=UUID("00000000-0000-0000-0000-000000000001"),
            s3_key="papers/paper.pdf",
            name="paper.pdf",
            category="LLM",
            status="indexed",
            s3_uploaded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            rag_indexed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        ),
    )

    result = await StaticIndexedFileQueryRepository(files).list_indexed_files()

    assert result == files
