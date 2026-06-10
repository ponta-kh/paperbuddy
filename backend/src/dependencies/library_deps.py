from functools import lru_cache

from src.application.ports.input.library.list_indexed_files_protocol import (
    ListIndexedFilesProtocol,
)
from src.application.use_cases.library.list_indexed_files.list_indexed_files import (
    ListIndexedFilesUseCase,
)
from src.infrastructure.library.static_indexed_file_catalog import (
    StaticIndexedFileCatalog,
)


@lru_cache
def get_indexed_file_catalog() -> StaticIndexedFileCatalog:
    return StaticIndexedFileCatalog()


@lru_cache
def get_list_indexed_files_use_case() -> ListIndexedFilesProtocol:
    return ListIndexedFilesUseCase(get_indexed_file_catalog())
