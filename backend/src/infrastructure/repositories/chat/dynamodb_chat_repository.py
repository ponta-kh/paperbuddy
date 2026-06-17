import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, TypeGuard, cast
from uuid import UUID

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

from src.application.exceptions import RepositoryAccessError, RepositoryNotFoundError
from src.application.ports.out.chat import ChatMessageRecord, ChatSummary
from src.domain.entities.chat.chat import (
    Chat,
    ChatCitation,
    ChatCitationSource,
    ChatMessage,
)
from src.domain.repositories.chat_command_repository_protocol import (
    ChatConflictError,
    ChatLoadError,
    ChatNotFoundError,
    ChatSaveError,
)
from src.domain.repositories.chat_deletion_repository_protocol import ChatDeleteError
from src.domain.repositories.chat_title_repository_protocol import ChatTitleUpdateError
from src.domain.value_objects.chat.prompt import Prompt

_CHAT_SORT_KEY = "CHAT"
_MESSAGE_SORT_KEY_PREFIX = "MESSAGE#"
_USER_INDEX_NAME = "gsi1"
_serializer = TypeSerializer()
_deserializer = TypeDeserializer()


class _DynamoDbChatRepositoryOperations:
    def __init__(self, client: Any, *, table_name: str) -> None:
        self._client = client
        self._table_name = table_name

    async def save_started_chat(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        items = (
            self._chat_item(chat),
            self._message_item(user_message),
            self._message_item(llm_message),
        )
        try:
            await asyncio.to_thread(
                self._client.transact_write_items,
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": self._serialize(item),
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    }
                    for item in items
                ],
            )
        except ClientError as error:
            raise ChatSaveError from error

    async def get_chat(self, *, chat_id: UUID) -> Chat:
        try:
            item = await self._get_chat_item(chat_id)
        except ClientError as error:
            raise ChatLoadError from error
        if item is None:
            raise ChatNotFoundError
        return self._to_chat(item)

    async def save_exchange(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        chat_item = self._chat_item(chat)
        message_items = (
            self._message_item(user_message),
            self._message_item(llm_message),
        )
        try:
            await asyncio.to_thread(
                self._client.transact_write_items,
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": self._serialize(chat_item),
                            "ConditionExpression": (
                                "#version = :expected_version AND #user_id = :user_id"
                            ),
                            "ExpressionAttributeNames": {
                                "#version": "version",
                                "#user_id": "user_id",
                            },
                            "ExpressionAttributeValues": self._serialize(
                                {
                                    ":expected_version": chat.version - 1,
                                    ":user_id": str(chat.user_id),
                                }
                            ),
                        }
                    },
                    *[
                        {
                            "Put": {
                                "TableName": self._table_name,
                                "Item": self._serialize(item),
                                "ConditionExpression": "attribute_not_exists(pk)",
                            }
                        }
                        for item in message_items
                    ],
                ],
            )
        except ClientError as error:
            cancellation_reasons = self._cancellation_reasons(error)
            if any(
                reason.get("Code") == "ConditionalCheckFailed"
                for reason in cancellation_reasons
            ):
                raise ChatConflictError from error
            raise ChatSaveError from error

    async def update_title(
        self,
        *,
        chat_id: UUID,
        user_id: UUID,
        title: str,
    ) -> None:
        try:
            # 所有者条件を更新式に含め、
            # 存在有無と所有者不一致を同じNotFoundとして扱う。
            await asyncio.to_thread(
                self._client.update_item,
                TableName=self._table_name,
                Key=self._serialize(
                    {"pk": self._chat_key(chat_id), "sk": _CHAT_SORT_KEY}
                ),
                UpdateExpression="SET #title = :title",
                ConditionExpression="attribute_exists(pk) AND #user_id = :user_id",
                ExpressionAttributeNames={"#title": "title", "#user_id": "user_id"},
                ExpressionAttributeValues=self._serialize(
                    {":title": title, ":user_id": str(user_id)}
                ),
            )
        except ClientError as error:
            if self._client_error_code(error) == "ConditionalCheckFailedException":
                raise ChatNotFoundError from error
            raise ChatTitleUpdateError from error

    async def delete_chat(self, *, chat_id: UUID, user_id: UUID) -> None:
        try:
            chat_item = await self._get_chat_item(chat_id)
            if chat_item is None or chat_item["user_id"] != str(user_id):
                raise ChatNotFoundError
            items = await self._query_all(
                TableName=self._table_name,
                KeyConditionExpression="pk = :chat_key",
                ExpressionAttributeValues=self._serialize(
                    {":chat_key": self._chat_key(chat_id)}
                ),
                ProjectionExpression="pk, sk",
                ConsistentRead=True,
            )
            for start in range(0, len(items), 25):
                # DynamoDB BatchWriteItemの上限に合わせて分割する。
                # 複数バッチは原子的ではない。
                delete_requests = [
                    {
                        "DeleteRequest": {
                            "Key": self._serialize({"pk": item["pk"], "sk": item["sk"]})
                        }
                    }
                    for item in items[start : start + 25]
                ]
                response = await asyncio.to_thread(
                    self._client.batch_write_item,
                    RequestItems={self._table_name: delete_requests},
                )
                if response.get("UnprocessedItems"):
                    raise ChatDeleteError
        except ChatDeleteError:
            raise
        except ChatNotFoundError:
            raise
        except ClientError as error:
            raise ChatDeleteError from error

    async def list_chats_by_user_id(self, user_id: UUID) -> tuple[ChatSummary, ...]:
        try:
            items = await self._query_all(
                TableName=self._table_name,
                IndexName=_USER_INDEX_NAME,
                KeyConditionExpression="gsi1pk = :user_key",
                ExpressionAttributeValues=self._serialize(
                    {":user_key": self._user_key(user_id)}
                ),
                ScanIndexForward=False,
            )
        except ClientError as error:
            raise RepositoryAccessError from error

        if not items:
            raise RepositoryNotFoundError
        return tuple(
            ChatSummary(
                chat_id=UUID(item["chat_id"]),
                title=item["title"],
                created_at=self._parse_datetime(item["created_at"]),
                last_updated_at=self._parse_datetime(item["last_updated_at"]),
            )
            for item in items
        )

    async def list_messages_by_chat_id(
        self,
        *,
        user_id: UUID,
        chat_id: UUID,
    ) -> tuple[ChatMessageRecord, ...]:
        try:
            chat_item = await self._get_chat_item(chat_id)
            if chat_item is None or chat_item["user_id"] != str(user_id):
                raise RepositoryNotFoundError
            items = await self._query_all(
                TableName=self._table_name,
                KeyConditionExpression="pk = :chat_key AND begins_with(sk, :message_prefix)",
                ExpressionAttributeValues=self._serialize(
                    {
                        ":chat_key": self._chat_key(chat_id),
                        ":message_prefix": _MESSAGE_SORT_KEY_PREFIX,
                    }
                ),
                ScanIndexForward=True,
                ConsistentRead=True,
            )
        except RepositoryNotFoundError:
            raise
        except ClientError as error:
            raise RepositoryAccessError from error

        if not items:
            raise RepositoryNotFoundError
        return tuple(
            ChatMessageRecord(
                request_id=UUID(item["request_id"]),
                sender=item["sender"],
                content=item["content"],
                sent_at=self._parse_datetime(item["sent_at"]),
                citations=self._to_citations(item.get("citations", [])),
            )
            for item in items
        )

    async def _get_chat_item(self, chat_id: UUID) -> dict[str, Any] | None:
        response = await asyncio.to_thread(
            self._client.get_item,
            TableName=self._table_name,
            Key=self._serialize({"pk": self._chat_key(chat_id), "sk": _CHAT_SORT_KEY}),
            ConsistentRead=True,
        )
        item = response.get("Item")
        return self._deserialize(item) if item is not None else None

    async def _query_all(self, **request: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        while True:
            response = await asyncio.to_thread(self._client.query, **request)
            items.extend(self._deserialize(item) for item in response.get("Items", []))
            last_evaluated_key = response.get("LastEvaluatedKey")
            if last_evaluated_key is None:
                return items
            # 呼び出し側へDynamoDBのページ境界を見せず、
            # ポート契約上は全件取得として扱う。
            request["ExclusiveStartKey"] = last_evaluated_key

    @classmethod
    def _chat_item(cls, chat: Chat) -> dict[str, Any]:
        return {
            "pk": cls._chat_key(chat.chat_id),
            "sk": _CHAT_SORT_KEY,
            "entity_type": "chat",
            "chat_id": str(chat.chat_id),
            "session_id": chat.session_id,
            "title": chat.title,
            "user_id": str(chat.user_id),
            "created_at": cls._format_datetime(chat.created_at),
            "last_updated_at": cls._format_datetime(chat.last_updated_at),
            "version": chat.version,
            "gsi1pk": cls._user_key(chat.user_id),
            "gsi1sk": (
                f"UPDATED#{cls._format_datetime(chat.last_updated_at)}#{chat.chat_id}"
            ),
        }

    @classmethod
    def _message_item(cls, message: ChatMessage) -> dict[str, Any]:
        # 同一発信日時でも履歴取得時に、
        # ユーザー発信、LLM回答の順になるようにする。
        sender_order = "0" if message.sender.value == "user" else "1"
        sent_at = cls._format_datetime(message.sent_at)
        content = (
            message.content.value
            if isinstance(message.content, Prompt)
            else message.content
        )
        return {
            "pk": cls._chat_key(message.chat_id),
            "sk": (
                f"{_MESSAGE_SORT_KEY_PREFIX}{sent_at}#"
                f"{message.request_id}#{sender_order}"
            ),
            "entity_type": "message",
            "chat_id": str(message.chat_id),
            "request_id": str(message.request_id),
            "sender": message.sender.value,
            "content": content,
            "citations": cls._citation_items(message.citations),
            "sent_at": sent_at,
        }

    @staticmethod
    def _citation_items(citations: tuple[ChatCitation, ...]) -> list[dict[str, Any]]:
        return [
            {
                "text": citation.text,
                "span_start": citation.span_start,
                "span_end": citation.span_end,
                "sources": [
                    {
                        "content": source.content,
                        "location_type": source.location_type,
                        "uri": source.uri,
                        "metadata": source.metadata,
                    }
                    for source in citation.sources
                ],
            }
            for citation in citations
        ]

    @classmethod
    def _to_citations(cls, value: object) -> tuple[ChatCitation, ...]:
        if not isinstance(value, list):
            return ()
        return tuple(
            cls._to_citation(item) for item in value if cls._is_str_mapping(item)
        )

    @classmethod
    def _to_citation(cls, item: Mapping[str, object]) -> ChatCitation:
        sources = item.get("sources", [])
        if not isinstance(sources, list):
            sources = []
        return ChatCitation(
            text=cls._optional_str(item.get("text")) or "",
            span_start=cls._optional_int(item.get("span_start")),
            span_end=cls._optional_int(item.get("span_end")),
            sources=tuple(
                cls._to_citation_source(source)
                for source in sources
                if cls._is_str_mapping(source)
            ),
        )

    @classmethod
    def _to_citation_source(cls, item: Mapping[str, object]) -> ChatCitationSource:
        metadata = item.get("metadata", {})
        if not isinstance(metadata, Mapping):
            metadata = {}
        location_type = item.get("location_type")
        uri = item.get("uri")
        return ChatCitationSource(
            content=cls._optional_str(item.get("content")) or "",
            location_type=location_type if isinstance(location_type, str) else None,
            uri=uri if isinstance(uri, str) else None,
            metadata=dict(metadata),
        )

    @staticmethod
    def _optional_str(value: object) -> str | None:
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _is_str_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
        return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, Decimal):
            return int(value)
        return None

    @staticmethod
    def _to_chat(item: dict[str, Any]) -> Chat:
        return Chat(
            chat_id=UUID(item["chat_id"]),
            session_id=item["session_id"],
            title=item["title"],
            user_id=UUID(item["user_id"]),
            created_at=_DynamoDbChatRepositoryOperations._parse_datetime(
                item["created_at"]
            ),
            last_updated_at=_DynamoDbChatRepositoryOperations._parse_datetime(
                item["last_updated_at"]
            ),
            version=item["version"],
        )

    @staticmethod
    def _chat_key(chat_id: UUID) -> str:
        return f"CHAT#{chat_id}"

    @staticmethod
    def _user_key(user_id: UUID) -> str:
        return f"USER#{user_id}"

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _serialize(item: dict[str, Any]) -> dict[str, Any]:
        return {key: _serializer.serialize(value) for key, value in item.items()}

    @staticmethod
    def _deserialize(item: dict[str, Any]) -> dict[str, Any]:
        return {key: _deserializer.deserialize(value) for key, value in item.items()}

    @staticmethod
    def _client_error_code(error: ClientError) -> str:
        response = cast(dict[str, Any], error.response)
        error_detail = response.get("Error", {})
        if not isinstance(error_detail, dict):
            return ""
        return str(error_detail.get("Code", ""))

    @staticmethod
    def _cancellation_reasons(error: ClientError) -> list[dict[str, Any]]:
        response = cast(dict[str, Any], error.response)
        reasons = response.get("CancellationReasons", [])
        if not isinstance(reasons, list):
            return []
        return [reason for reason in reasons if isinstance(reason, dict)]


class _DynamoDbChatRepository:
    def __init__(self, client: Any, *, table_name: str) -> None:
        self._operations = _DynamoDbChatRepositoryOperations(
            client,
            table_name=table_name,
        )


class DynamoDbChatCommandRepository(_DynamoDbChatRepository):
    """DynamoDBへチャット集約とメッセージを保存するCommand Repository実装。"""

    async def save_started_chat(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        """チャット本体と初回ターンの2メッセージをトランザクション保存する。

        Raises:
            ChatSaveError: DynamoDBへの保存に失敗した場合。
        """

        await self._operations.save_started_chat(chat, user_message, llm_message)

    async def get_chat(self, *, chat_id: UUID) -> Chat:
        """チャット本体をDynamoDBから取得してDomain Entityへ復元する。

        Raises:
            ChatNotFoundError: 指定チャットが存在しない場合。
            ChatLoadError: DynamoDBからの読み込みに失敗した場合。
        """

        return await self._operations.get_chat(chat_id=chat_id)

    async def save_exchange(
        self,
        chat: Chat,
        user_message: ChatMessage,
        llm_message: ChatMessage,
    ) -> None:
        """更新後チャット本体と継続ターンの2メッセージをトランザクション保存する。

        Raises:
            ChatConflictError: 保存済みチャットのバージョンと競合した場合。
            ChatSaveError: DynamoDBへの保存に失敗した場合。
        """

        await self._operations.save_exchange(chat, user_message, llm_message)


class DynamoDbChatQueryRepository(_DynamoDbChatRepository):
    """DynamoDBからチャット読み取りモデルを取得するQuery Repository実装。"""

    async def list_chats_by_user_id(self, user_id: UUID) -> tuple[ChatSummary, ...]:
        """GSIを使って指定ユーザーのチャット一覧を取得する。

        Raises:
            RepositoryNotFoundError: 指定ユーザーのチャットが存在しない場合。
            RepositoryAccessError: DynamoDBからの読み込みまたは項目変換に失敗した場合。
        """

        return await self._operations.list_chats_by_user_id(user_id)

    async def list_messages_by_chat_id(
        self,
        *,
        user_id: UUID,
        chat_id: UUID,
    ) -> tuple[ChatMessageRecord, ...]:
        """指定チャットのメッセージ履歴を送信日時順で取得する。

        DynamoDB上の引用情報はMap/ListからDomainの引用情報へ復元する。

        Raises:
            RepositoryNotFoundError: 指定チャットまたはメッセージが存在しない場合。
            RepositoryAccessError: DynamoDBからの読み込みまたは項目変換に失敗した場合。
        """

        return await self._operations.list_messages_by_chat_id(
            user_id=user_id,
            chat_id=chat_id,
        )


class DynamoDbChatTitleRepository(_DynamoDbChatRepository):
    """DynamoDB上のチャットタイトルを更新するRepository実装。"""

    async def update_title(
        self,
        *,
        chat_id: UUID,
        user_id: UUID,
        title: str,
    ) -> None:
        """所有者条件つきでチャットタイトルを更新する。

        Raises:
            ChatTitleUpdateError: DynamoDBでタイトル更新に失敗した場合。
        """

        await self._operations.update_title(
            chat_id=chat_id,
            user_id=user_id,
            title=title,
        )


class DynamoDbChatDeletionRepository(_DynamoDbChatRepository):
    """DynamoDB上のチャット本体とメッセージを削除するRepository実装。"""

    async def delete_chat(self, *, chat_id: UUID, user_id: UUID) -> None:
        """所有者条件つきでチャット本体とメッセージ履歴を削除する。

        Raises:
            ChatDeleteError: DynamoDBでチャット削除に失敗した場合。
        """

        await self._operations.delete_chat(chat_id=chat_id, user_id=user_id)
