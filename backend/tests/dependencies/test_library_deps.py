from collections.abc import Iterator
from unittest.mock import Mock

import pytest

from src.application.use_cases.library.list_indexed_files.list_indexed_files import (
    ListIndexedFilesUseCase,
)
from src.dependencies import client_factories, library_deps
from src.dependencies.settings import get_settings
from src.infrastructure.library.dynamodb_indexed_file_catalog import (
    DynamoDbIndexedFileCatalog,
)


@pytest.fixture(autouse=True)
def clear_cached_dependencies() -> Iterator[None]:
    library_deps.get_indexed_file_catalog.cache_clear()
    library_deps.get_list_indexed_files_use_case.cache_clear()
    get_settings.cache_clear()
    yield
    library_deps.get_indexed_file_catalog.cache_clear()
    library_deps.get_list_indexed_files_use_case.cache_clear()
    get_settings.cache_clear()


def _set_aws_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv("DYNAMODB_CHAT_TABLE_NAME", "chat-table")
    monkeypatch.setenv("DYNAMODB_LIBRARY_TABLE_NAME", "library-table")
    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "knowledge-base-id")
    monkeypatch.setenv("BEDROCK_MODEL_ARN", "model-arn")


def _set_local_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAT_INFRASTRUCTURE_MODE", "local")
    monkeypatch.setenv("AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv("DYNAMODB_CHAT_TABLE_NAME", "chat-table")
    monkeypatch.setenv("DYNAMODB_LIBRARY_TABLE_NAME", "library-table")
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", "http://dynamodb-local:8000")


def test_get_library_dependencies_use_dynamodb_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_aws_environment(monkeypatch)
    dynamodb_client = Mock()
    client_factory = Mock(return_value=dynamodb_client)
    monkeypatch.setattr(client_factories.boto3, "client", client_factory)

    catalog = library_deps.get_indexed_file_catalog()
    use_case = library_deps.get_list_indexed_files_use_case()

    assert isinstance(catalog, DynamoDbIndexedFileCatalog)
    assert isinstance(use_case, ListIndexedFilesUseCase)
    assert client_factory.call_args == (
        ("dynamodb",),
        {"region_name": "ap-northeast-1"},
    )


def test_get_library_dependencies_use_dynamodb_local_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_local_environment(monkeypatch)
    dynamodb_client = Mock()
    client_factory = Mock(return_value=dynamodb_client)
    monkeypatch.setattr(client_factories.boto3, "client", client_factory)

    catalog = library_deps.get_indexed_file_catalog()

    assert isinstance(catalog, DynamoDbIndexedFileCatalog)
    assert client_factory.call_args == (
        ("dynamodb",),
        {
            "region_name": "ap-northeast-1",
            "endpoint_url": "http://dynamodb-local:8000",
        },
    )
