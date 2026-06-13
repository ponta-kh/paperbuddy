from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import UUID

import pytest
from botocore.exceptions import ClientError

from src.application.exceptions import RepositoryAccessError, RepositoryNotFoundError
from src.domain.entities.chat.chat import Chat, ChatMessage
from src.domain.repositories.chat_command_repository_protocol import (
    ChatConflictError,
    ChatLoadError,
    ChatNotFoundError,
    ChatSaveError,
)
from src.domain.repositories.chat_deletion_repository_protocol import ChatDeleteError
from src.domain.repositories.chat_title_repository_protocol import ChatTitleUpdateError
from src.domain.value_objects.chat.chat_turn_id import ChatTurnId
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt
from src.infrastructure.repositories.chat.dynamodb_chat_repository import (
    _DynamoDbChatRepositoryOperations as DynamoDbChatRepository,
)

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
ANSWERED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
CHAT_ID = UUID("10000000-0000-0000-0000-000000000001")
SECOND_CHAT_ID = UUID("10000000-0000-0000-0000-000000000002")


def _chat() -> Chat:
    return Chat.create(
        chat_id=CHAT_ID,
        session_id="session-1",
        title="title",
        user_id=USER_ID,
        answered_at=ANSWERED_AT,
    )


def _messages(
    *,
    user_sent_at: datetime = ANSWERED_AT,
    llm_sent_at: datetime = ANSWERED_AT,
) -> tuple[ChatMessage, ChatMessage]:
    turn_id = ChatTurnId(UUID("00000000-0000-0000-0000-000000000010"))
    return (
        ChatMessage(
            CHAT_ID,
            turn_id,
            MessageSender.USER,
            Prompt("question"),
            user_sent_at,
        ),
        ChatMessage(CHAT_ID, turn_id, MessageSender.LLM, "answer", llm_sent_at),
    )


def _client_error(
    code: str,
    *,
    cancellation_reasons: list[dict[str, str]] | None = None,
) -> ClientError:
    response: dict[str, object] = {"Error": {"Code": code, "Message": "failed"}}
    if cancellation_reasons is not None:
        response["CancellationReasons"] = cancellation_reasons
    return ClientError(response, "operation")


def _serialized_chat_item(repository: DynamoDbChatRepository) -> dict[str, object]:
    return repository._serialize(repository._chat_item(_chat()))


@pytest.mark.asyncio
async def test_save_started_chat_writes_chat_and_messages_atomically() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    await repository.save_started_chat(_chat(), *_messages())

    transaction = client.transact_write_items.call_args.kwargs["TransactItems"]
    assert len(transaction) == 3
    assert all(
        item["Put"]["ConditionExpression"] == "attribute_not_exists(pk)"
        for item in transaction
    )
    stored = [repository._deserialize(item["Put"]["Item"]) for item in transaction]
    assert stored[0]["pk"] == f"CHAT#{CHAT_ID}"
    assert stored[0]["session_id"] == "session-1"
    assert stored[0]["gsi1pk"] == f"USER#{USER_ID}"
    assert [item["sender"] for item in stored[1:]] == ["user", "llm"]
    assert stored[1]["sk"] < stored[2]["sk"]


@pytest.mark.asyncio
async def test_save_started_chat_converts_client_error() -> None:
    client = Mock()
    client.transact_write_items.side_effect = _client_error("InternalServerError")
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatSaveError):
        await repository.save_started_chat(_chat(), *_messages())


@pytest.mark.asyncio
async def test_get_chat_for_continuation_returns_domain_entity() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    client.get_item.return_value = {"Item": _serialized_chat_item(repository)}

    chat = await repository.get_chat_for_continuation(chat_id=CHAT_ID, user_id=USER_ID)

    assert chat.chat_id == CHAT_ID
    assert chat.session_id == "session-1"
    assert chat.user_id == USER_ID
    assert chat.created_at == ANSWERED_AT
    assert chat.version == 0
    assert client.get_item.call_args.kwargs["ConsistentRead"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {},
        pytest.param(
            {
                "Item": DynamoDbChatRepository._serialize(
                    {
                        **DynamoDbChatRepository._chat_item(_chat()),
                        "user_id": str(OTHER_USER_ID),
                    }
                )
            },
            id="other-user",
        ),
    ],
)
async def test_get_chat_for_continuation_hides_missing_or_other_users_chat(
    response: dict[str, object],
) -> None:
    client = Mock()
    client.get_item.return_value = response
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatNotFoundError):
        await repository.get_chat_for_continuation(chat_id=CHAT_ID, user_id=USER_ID)


@pytest.mark.asyncio
async def test_get_chat_for_continuation_converts_client_error() -> None:
    client = Mock()
    client.get_item.side_effect = _client_error("InternalServerError")
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatLoadError):
        await repository.get_chat_for_continuation(chat_id=CHAT_ID, user_id=USER_ID)


@pytest.mark.asyncio
async def test_save_exchange_checks_previous_version_and_owner() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    chat = _chat()
    messages = _messages(
        user_sent_at=ANSWERED_AT + timedelta(seconds=1),
        llm_sent_at=ANSWERED_AT + timedelta(seconds=2),
    )
    chat.record_exchange(user_message=messages[0], llm_message=messages[1])

    await repository.save_exchange(chat, *messages)

    put = client.transact_write_items.call_args.kwargs["TransactItems"][0]["Put"]
    values = repository._deserialize(put["ExpressionAttributeValues"])
    assert values == {":expected_version": 0, ":user_id": str(USER_ID)}
    assert "#version = :expected_version" in put["ConditionExpression"]


@pytest.mark.asyncio
async def test_save_exchange_converts_transaction_cancellation_to_conflict() -> None:
    client = Mock()
    client.transact_write_items.side_effect = _client_error(
        "TransactionCanceledException",
        cancellation_reasons=[{"Code": "ConditionalCheckFailed"}],
    )
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatConflictError):
        await repository.save_exchange(_chat(), *_messages())


@pytest.mark.asyncio
async def test_save_exchange_converts_non_conditional_cancellation_to_save_error() -> (
    None
):
    client = Mock()
    client.transact_write_items.side_effect = _client_error(
        "TransactionCanceledException",
        cancellation_reasons=[{"Code": "ProvisionedThroughputExceeded"}],
    )
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatSaveError):
        await repository.save_exchange(_chat(), *_messages())


@pytest.mark.asyncio
async def test_update_title_updates_owned_chat() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    await repository.update_title(chat_id=CHAT_ID, user_id=USER_ID, title="変更後")

    request = client.update_item.call_args.kwargs
    assert repository._deserialize(request["Key"]) == {
        "pk": f"CHAT#{CHAT_ID}",
        "sk": "CHAT",
    }
    assert repository._deserialize(request["ExpressionAttributeValues"]) == {
        ":title": "変更後",
        ":user_id": str(USER_ID),
    }
    assert "#user_id = :user_id" in request["ConditionExpression"]


@pytest.mark.asyncio
async def test_update_title_hides_missing_or_other_users_chat() -> None:
    client = Mock()
    client.update_item.side_effect = _client_error("ConditionalCheckFailedException")
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatNotFoundError):
        await repository.update_title(chat_id=CHAT_ID, user_id=USER_ID, title="変更後")


@pytest.mark.asyncio
async def test_update_title_converts_client_error() -> None:
    client = Mock()
    client.update_item.side_effect = _client_error("InternalServerError")
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatTitleUpdateError):
        await repository.update_title(chat_id=CHAT_ID, user_id=USER_ID, title="変更後")


@pytest.mark.asyncio
async def test_delete_chat_deletes_all_items_in_batches_of_25() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    items = [
        repository._serialize({"pk": f"CHAT#{CHAT_ID}", "sk": f"ITEM#{index:02}"})
        for index in range(26)
    ]
    client.query.return_value = {"Items": items}
    client.get_item.return_value = {"Item": _serialized_chat_item(repository)}
    client.batch_write_item.return_value = {}

    await repository.delete_chat(chat_id=CHAT_ID, user_id=USER_ID)

    query = client.query.call_args.kwargs
    assert query["ProjectionExpression"] == "pk, sk"
    assert query["ConsistentRead"] is True
    assert client.batch_write_item.call_count == 2
    assert (
        len(
            client.batch_write_item.call_args_list[0].kwargs["RequestItems"][
                "chat-table"
            ]
        )
        == 25
    )
    assert (
        len(
            client.batch_write_item.call_args_list[1].kwargs["RequestItems"][
                "chat-table"
            ]
        )
        == 1
    )


@pytest.mark.asyncio
async def test_delete_chat_succeeds_when_chat_has_no_items() -> None:
    client = Mock()
    client.query.return_value = {"Items": []}
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    client.get_item.return_value = {"Item": _serialized_chat_item(repository)}

    await repository.delete_chat(chat_id=CHAT_ID, user_id=USER_ID)

    client.batch_write_item.assert_not_called()


@pytest.mark.asyncio
async def test_delete_chat_rejects_unprocessed_items() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    item = repository._serialize({"pk": f"CHAT#{CHAT_ID}", "sk": "CHAT"})
    client.get_item.return_value = {"Item": _serialized_chat_item(repository)}
    client.query.return_value = {"Items": [item]}
    client.batch_write_item.return_value = {
        "UnprocessedItems": {"chat-table": [{"DeleteRequest": {"Key": item}}]}
    }

    with pytest.raises(ChatDeleteError):
        await repository.delete_chat(chat_id=CHAT_ID, user_id=USER_ID)


@pytest.mark.asyncio
async def test_delete_chat_converts_client_error() -> None:
    client = Mock()
    client.get_item.side_effect = _client_error("InternalServerError")
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatDeleteError):
        await repository.delete_chat(chat_id=CHAT_ID, user_id=USER_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {},
        pytest.param(
            {
                "Item": DynamoDbChatRepository._serialize(
                    {
                        **DynamoDbChatRepository._chat_item(_chat()),
                        "user_id": str(OTHER_USER_ID),
                    }
                )
            },
            id="other-user",
        ),
    ],
)
async def test_delete_chat_hides_missing_or_other_users_chat(
    response: dict[str, object],
) -> None:
    client = Mock()
    client.get_item.return_value = response
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(ChatNotFoundError):
        await repository.delete_chat(chat_id=CHAT_ID, user_id=USER_ID)

    client.query.assert_not_called()
    client.batch_write_item.assert_not_called()


@pytest.mark.asyncio
async def test_list_chats_queries_user_index_in_descending_order() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    client.query.return_value = {"Items": [_serialized_chat_item(repository)]}

    chats = await repository.list_chats_by_user_id(USER_ID)

    assert [chat.chat_id for chat in chats] == [CHAT_ID]
    query = client.query.call_args.kwargs
    assert query["IndexName"] == "gsi1"
    assert query["ScanIndexForward"] is False


@pytest.mark.asyncio
async def test_list_chats_reads_all_query_pages() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    first = repository._chat_item(_chat())
    second = {
        **first,
        "chat_id": str(SECOND_CHAT_ID),
        "pk": f"CHAT#{SECOND_CHAT_ID}",
    }
    last_evaluated_key = repository._serialize({"pk": f"CHAT#{CHAT_ID}", "sk": "CHAT"})
    client.query.side_effect = [
        {
            "Items": [repository._serialize(first)],
            "LastEvaluatedKey": last_evaluated_key,
        },
        {"Items": [repository._serialize(second)]},
    ]

    chats = await repository.list_chats_by_user_id(USER_ID)

    assert [chat.chat_id for chat in chats] == [CHAT_ID, SECOND_CHAT_ID]
    assert (
        client.query.call_args_list[1].kwargs["ExclusiveStartKey"] == last_evaluated_key
    )


@pytest.mark.asyncio
async def test_list_chats_raises_not_found_when_empty() -> None:
    client = Mock()
    client.query.return_value = {"Items": []}
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(RepositoryNotFoundError):
        await repository.list_chats_by_user_id(USER_ID)


@pytest.mark.asyncio
async def test_list_messages_checks_owner_and_returns_records() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    message_items = [
        repository._serialize(repository._message_item(message))
        for message in _messages()
    ]
    client.get_item.return_value = {"Item": _serialized_chat_item(repository)}
    client.query.return_value = {"Items": message_items}

    messages = await repository.list_messages_by_chat_id(
        user_id=USER_ID, chat_id=CHAT_ID
    )

    assert [message.sender for message in messages] == ["user", "llm"]
    assert [message.content for message in messages] == ["question", "answer"]
    assert client.query.call_args.kwargs["ConsistentRead"] is True


@pytest.mark.asyncio
async def test_list_messages_hides_other_users_chat_without_querying_messages() -> None:
    client = Mock()
    repository = DynamoDbChatRepository(client, table_name="chat-table")
    other_user_item = {
        **repository._chat_item(_chat()),
        "user_id": str(OTHER_USER_ID),
    }
    client.get_item.return_value = {"Item": repository._serialize(other_user_item)}

    with pytest.raises(RepositoryNotFoundError):
        await repository.list_messages_by_chat_id(user_id=USER_ID, chat_id=CHAT_ID)

    client.query.assert_not_called()


@pytest.mark.asyncio
async def test_query_operations_convert_client_error() -> None:
    client = Mock()
    client.query.side_effect = _client_error("InternalServerError")
    repository = DynamoDbChatRepository(client, table_name="chat-table")

    with pytest.raises(RepositoryAccessError):
        await repository.list_chats_by_user_id(USER_ID)
