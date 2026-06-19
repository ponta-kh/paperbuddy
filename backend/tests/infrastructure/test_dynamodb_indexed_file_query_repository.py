from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import UUID

import pytest
from botocore.exceptions import ClientError

from src.application.exceptions import RepositoryAccessError, RepositoryNotFoundError
from src.infrastructure.repositories.library.dynamodb_indexed_file_query_repository import (
    DynamoDbIndexedFileQueryRepository,
)


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "failed"}}, "scan")


def _item(
    *,
    source_id: str,
    s3_key: str,
    file_name: str,
    category: str,
    status: str,
    s3_uploaded_at: str,
    rag_indexed_at: str | None,
) -> dict[str, dict[str, str]]:
    item: dict[str, dict[str, str]] = {
        "source_id": {"S": source_id},
        "s3_key": {"S": s3_key},
        "file_name": {"S": file_name},
        "category": {"S": category},
        "status": {"S": status},
        "s3_uploaded_at": {"S": s3_uploaded_at},
    }
    if rag_indexed_at is not None:
        item["rag_indexed_at"] = {"S": rag_indexed_at}
    return item


@pytest.mark.asyncio
async def test_list_indexed_files_returns_all_items() -> None:
    client = Mock()
    client.scan.side_effect = [
        {
            "Items": [
                _item(
                    source_id="00000000-0000-0000-0000-000000000002",
                    s3_key="papers/b.pdf",
                    file_name="paper-b.pdf",
                    category="経済",
                    status="indexed",
                    s3_uploaded_at="2026-01-02T00:00:00Z",
                    rag_indexed_at="2026-01-03T00:00:00Z",
                )
            ],
            "LastEvaluatedKey": {"pk": {"S": "SOURCE#2"}, "sk": {"S": "SOURCE"}},
        },
        {
            "Items": [
                _item(
                    source_id="00000000-0000-0000-0000-000000000001",
                    s3_key="papers/a.pdf",
                    file_name="paper-a.pdf",
                    category="LLM",
                    status="processing",
                    s3_uploaded_at="2026-01-01T00:00:00Z",
                    rag_indexed_at=None,
                )
            ]
        },
    ]
    repository = DynamoDbIndexedFileQueryRepository(client, table_name="library-table")

    result = await repository.list_indexed_files()

    assert tuple(file.source_id for file in result) == (
        UUID("00000000-0000-0000-0000-000000000002"),
        UUID("00000000-0000-0000-0000-000000000001"),
    )
    assert result[0].s3_uploaded_at == datetime(2026, 1, 2, tzinfo=timezone.utc)
    assert result[1].rag_indexed_at is None
    assert client.scan.call_count == 2


@pytest.mark.asyncio
async def test_list_indexed_files_raises_not_found_when_empty() -> None:
    client = Mock()
    client.scan.return_value = {"Items": []}
    repository = DynamoDbIndexedFileQueryRepository(client, table_name="library-table")

    with pytest.raises(RepositoryNotFoundError):
        await repository.list_indexed_files()


@pytest.mark.asyncio
async def test_list_indexed_files_converts_client_error() -> None:
    client = Mock()
    client.scan.side_effect = _client_error("InternalServerError")
    repository = DynamoDbIndexedFileQueryRepository(client, table_name="library-table")

    with pytest.raises(RepositoryAccessError):
        await repository.list_indexed_files()
