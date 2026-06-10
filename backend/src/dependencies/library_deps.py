from functools import lru_cache

import boto3

from src.application.ports.input.library.list_indexed_files_protocol import (
    ListIndexedFilesProtocol,
)
from src.application.ports.out.indexed_file_catalog_protocol import (
    IndexedFileCatalogProtocol,
)
from src.application.use_cases.library.list_indexed_files.list_indexed_files import (
    ListIndexedFilesUseCase,
)
from src.dependencies.settings import ChatInfrastructureMode, get_settings
from src.infrastructure.library.dynamodb_indexed_file_catalog import (
    DynamoDbIndexedFileCatalog,
)


@lru_cache
def get_indexed_file_catalog() -> IndexedFileCatalogProtocol:
    settings = get_settings()
    client_options: dict[str, str] = {"region_name": settings.aws_region}
    if settings.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL:
        assert settings.dynamodb_endpoint_url is not None
        client_options["endpoint_url"] = settings.dynamodb_endpoint_url
    client = boto3.client("dynamodb", **client_options)
    return DynamoDbIndexedFileCatalog(
        client,
        table_name=settings.dynamodb_library_table_name,
    )


@lru_cache
def get_list_indexed_files_use_case() -> ListIndexedFilesProtocol:
    return ListIndexedFilesUseCase(get_indexed_file_catalog())
