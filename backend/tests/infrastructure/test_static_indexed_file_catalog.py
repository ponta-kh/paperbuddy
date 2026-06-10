import pytest

from src.application.ports.out.indexed_file_catalog_protocol import IndexedFile
from src.infrastructure.library.static_indexed_file_catalog import (
    StaticIndexedFileCatalog,
)


@pytest.mark.asyncio
async def test_static_indexed_file_catalog_returns_configured_files() -> None:
    files = (IndexedFile(name="paper.pdf"),)

    result = await StaticIndexedFileCatalog(files).list_indexed_files()

    assert result == files
