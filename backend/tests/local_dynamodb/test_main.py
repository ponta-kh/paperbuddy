from unittest.mock import Mock

import local_dynamodb.main as local_dynamodb_main


def test_main_initializes_tables_and_seeds_chat_data(monkeypatch) -> None:
    settings = Mock(
        dynamodb_chat_table_name="chat-table",
        dynamodb_library_table_name="library-table",
    )
    client = Mock()
    client.create_table.side_effect = [
        None,
        None,
    ]
    get_settings = Mock(return_value=settings)
    create_client = Mock(return_value=client)
    seed_local_chats = Mock()
    sleep = Mock()

    monkeypatch.setattr(local_dynamodb_main, "get_settings", get_settings)
    monkeypatch.setattr(
        local_dynamodb_main,
        "create_local_dynamodb_client",
        create_client,
    )
    monkeypatch.setattr(local_dynamodb_main, "seed_local_chats", seed_local_chats)
    monkeypatch.setattr(local_dynamodb_main.time, "sleep", sleep)

    local_dynamodb_main.main()

    create_client.assert_called_once_with(settings)
    seed_local_chats.assert_called_once_with(client, table_name="chat-table")
    sleep.assert_not_called()
