from functools import lru_cache

from src.application.ports.input.library.list_indexed_files_protocol import (
    ListIndexedFilesProtocol,
)
from src.application.ports.out.indexed_file_catalog_protocol import (
    IndexedFileCatalogProtocol,
)
from src.application.use_cases.library.list_indexed_files.list_indexed_files import (
    ListIndexedFilesUseCase,
)
from src.dependencies.client_factories import create_dynamodb_client
from src.dependencies.settings import get_settings
from src.infrastructure.library.dynamodb_indexed_file_catalog import (
    DynamoDbIndexedFileCatalog,
)


@lru_cache
def get_indexed_file_catalog() -> IndexedFileCatalogProtocol:
    """インデックス済みファイルCatalog実装を返すDIファクトリ。"""

    settings = get_settings()
    client = create_dynamodb_client(settings)
    return DynamoDbIndexedFileCatalog(
        client,
        table_name=settings.dynamodb_library_table_name,
    )


@lru_cache
def get_list_indexed_files_use_case() -> ListIndexedFilesProtocol:
    """インデックス済みファイル一覧取得ユースケースを返すDIファクトリ。"""

    return ListIndexedFilesUseCase(get_indexed_file_catalog())
