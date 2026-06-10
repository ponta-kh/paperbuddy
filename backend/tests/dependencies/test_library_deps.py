from src.application.use_cases.library.list_indexed_files.list_indexed_files import (
    ListIndexedFilesUseCase,
)
from src.dependencies.library_deps import (
    get_indexed_file_catalog,
    get_list_indexed_files_use_case,
)
from src.infrastructure.library.static_indexed_file_catalog import (
    StaticIndexedFileCatalog,
)


def test_library_dependencies_use_static_catalog() -> None:
    get_indexed_file_catalog.cache_clear()
    get_list_indexed_files_use_case.cache_clear()

    catalog = get_indexed_file_catalog()
    use_case = get_list_indexed_files_use_case()

    assert isinstance(catalog, StaticIndexedFileCatalog)
    assert isinstance(use_case, ListIndexedFilesUseCase)
