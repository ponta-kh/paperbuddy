import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

from src.application.exceptions import RepositoryAccessError, RepositoryNotFoundError
from src.application.ports.out.library.indexed_file_query_repository_protocol import (
    IndexedFile,
)

_deserializer = TypeDeserializer()


class DynamoDbIndexedFileQueryRepository:
    """DynamoDBからインデックス済みファイル一覧を取得するQuery Repository実装。"""

    def __init__(self, client: Any, *, table_name: str) -> None:
        self._client = client
        self._table_name = table_name

    async def list_indexed_files(self) -> tuple[IndexedFile, ...]:
        """DynamoDBテーブルをscanし、登録済みファイル一覧へ変換する。

        Raises:
            RepositoryNotFoundError: 登録済みファイルが存在しない場合。
            RepositoryAccessError: DynamoDBアクセスまたは項目変換に失敗した場合。
        """

        try:
            items = await self._scan_all()
        except ClientError as error:
            raise RepositoryAccessError from error

        if not items:
            raise RepositoryNotFoundError

        try:
            return tuple(self._to_indexed_file(item) for item in items)
        except (KeyError, TypeError, ValueError) as error:
            raise RepositoryAccessError from error

    async def _scan_all(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        scan_kwargs: dict[str, Any] = {
            "TableName": self._table_name,
            "ProjectionExpression": (
                "source_id, s3_key, paper_title, category, #status, "
                "s3_uploaded_at, rag_indexed_at"
            ),
            "ExpressionAttributeNames": {"#status": "status"},
        }

        while True:
            response = await asyncio.to_thread(self._client.scan, **scan_kwargs)
            items.extend(
                self._deserialize_item(item) for item in response.get("Items", [])
            )

            last_evaluated_key = response.get("LastEvaluatedKey")
            if last_evaluated_key is None:
                return items

            # ライブラリ一覧はポート契約上ページを持たないため、
            # DynamoDBの全ページを集約する。
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

    @staticmethod
    def _to_indexed_file(item: dict[str, Any]) -> IndexedFile:
        return IndexedFile(
            source_id=UUID(str(item["source_id"])),
            s3_key=str(item["s3_key"]),
            name=str(item["paper_title"]),
            category=str(item["category"]),
            status=str(item["status"]),
            s3_uploaded_at=DynamoDbIndexedFileQueryRepository._parse_datetime(
                item["s3_uploaded_at"]
            ),
            rag_indexed_at=DynamoDbIndexedFileQueryRepository._parse_nullable_datetime(
                item.get("rag_indexed_at")
            ),
        )

    @staticmethod
    def _parse_nullable_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        return DynamoDbIndexedFileQueryRepository._parse_datetime(value)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            # 既存データにタイムゾーンがない場合も、
            # 外側へはタイムゾーン付き日時だけを返す。
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    @staticmethod
    def _deserialize_item(item: dict[str, Any]) -> dict[str, Any]:
        return {key: _deserializer.deserialize(value) for key, value in item.items()}
