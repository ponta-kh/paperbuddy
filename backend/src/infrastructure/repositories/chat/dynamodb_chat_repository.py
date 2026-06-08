import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

from src.application.exceptions import RepositoryAccessError, RepositoryNotFoundError
from src.application.ports.out.chat import ChatMessageRecord, ChatSummary
from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.repositories.chat_command_repository_protocol import (
    ChatConflictError,
    ChatLoadError,
    ChatNotFoundError,
    ChatSaveError,
)
from src.domain.value_objects.chat.prompt import Prompt

_CHAT_SORT_KEY = "CHAT"
_MESSAGE_SORT_KEY_PREFIX = "MESSAGE#"
_USER_INDEX_NAME = "gsi1"
_serializer = TypeSerializer()
_deserializer = TypeDeserializer()


class DynamoDbChatRepository:
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

    async def get_chat_for_continuation(self, *, chat_id: UUID, user_id: UUID) -> Chat:
        try:
            item = await self._get_chat_item(chat_id)
        except ClientError as error:
            raise ChatLoadError from error
        if item is None or item["user_id"] != str(user_id):
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
            cancellation_reasons = error.response.get("CancellationReasons", [])
            if any(
                reason.get("Code") == "ConditionalCheckFailed"
                for reason in cancellation_reasons
            ):
                raise ChatConflictError from error
            raise ChatSaveError from error

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
                turn_id=UUID(item["turn_id"]),
                sender=item["sender"],
                content=item["content"],
                sent_at=self._parse_datetime(item["sent_at"]),
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
                f"{message.turn_id.value}#{sender_order}"
            ),
            "entity_type": "message",
            "chat_id": str(message.chat_id),
            "turn_id": str(message.turn_id.value),
            "sender": message.sender.value,
            "content": content,
            "sent_at": sent_at,
        }

    @staticmethod
    def _to_chat(item: dict[str, Any]) -> Chat:
        return Chat(
            chat_id=UUID(item["chat_id"]),
            session_id=item["session_id"],
            title=item["title"],
            user_id=UUID(item["user_id"]),
            created_at=DynamoDbChatRepository._parse_datetime(item["created_at"]),
            last_updated_at=DynamoDbChatRepository._parse_datetime(
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
