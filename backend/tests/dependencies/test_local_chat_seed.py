from collections import Counter
from datetime import datetime, timedelta
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from boto3.dynamodb.types import TypeDeserializer

from src.dependencies.local_chat_seed import build_seed_items, seed_local_chats

_JST = ZoneInfo("Asia/Tokyo")
_deserializer = TypeDeserializer()


def test_build_seed_items_creates_expected_chat_groups_and_histories() -> None:
    now = datetime(2026, 6, 10, 12, 0, tzinfo=_JST)

    items = build_seed_items(now=now)

    chats = [item for item in items if item["entity_type"] == "chat"]
    messages = [item for item in items if item["entity_type"] == "message"]
    start_of_today = datetime(2026, 6, 10, tzinfo=_JST)
    seven_days_ago = start_of_today - timedelta(days=7)
    groups = Counter(
        "today"
        if datetime.fromisoformat(chat["last_updated_at"].replace("Z", "+00:00"))
        >= start_of_today
        else "recent"
        if datetime.fromisoformat(chat["last_updated_at"].replace("Z", "+00:00"))
        >= seven_days_ago
        else "older"
        for chat in chats
    )

    assert groups == {"today": 2, "recent": 3, "older": 6}
    assert len(chats) == 11
    assert len(messages) == 44
    assert Counter(message["sender"] for message in messages) == {
        "user": 22,
        "llm": 22,
    }
    assert all(
        len([message for message in messages if message["chat_id"] == chat["chat_id"]])
        == 4
        for chat in chats
    )


def test_seed_local_chats_puts_all_items_idempotently() -> None:
    client = Mock()
    client.query.return_value = {"Items": []}
    now = datetime(2026, 6, 10, 12, 0, tzinfo=_JST)

    seed_local_chats(client, table_name="chat-table", now=now)
    seed_local_chats(client, table_name="chat-table", now=now)

    assert client.put_item.call_count == 110
    first_item = client.put_item.call_args_list[0].kwargs
    repeated_item = client.put_item.call_args_list[55].kwargs
    assert first_item == repeated_item
    assert first_item["TableName"] == "chat-table"
    assert _deserialize(first_item["Item"])["title"] == "Transformerの最新動向"


def test_seed_local_chats_removes_previous_seed_history_before_putting() -> None:
    client = Mock()
    client.query.return_value = {
        "Items": [
            {
                "pk": {"S": "CHAT#00000000-0000-0000-0000-000000000001"},
                "sk": {"S": "MESSAGE#old"},
            }
        ]
    }

    seed_local_chats(
        client,
        table_name="chat-table",
        now=datetime(2026, 6, 10, 12, 0, tzinfo=_JST),
    )

    assert client.delete_item.call_count == 11
    assert client.delete_item.call_args_list[0].kwargs == {
        "TableName": "chat-table",
        "Key": {
            "pk": {"S": "CHAT#00000000-0000-0000-0000-000000000001"},
            "sk": {"S": "MESSAGE#old"},
        },
    }


def _deserialize(item: dict) -> dict:
    return {key: _deserializer.deserialize(value) for key, value in item.items()}
