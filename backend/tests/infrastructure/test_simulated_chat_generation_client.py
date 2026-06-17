from uuid import UUID

import pytest

from src.infrastructure.llm.simulated_chat_generation_client import (
    SimulatedChatGenerationClient,
)


def test_rejects_negative_delay() -> None:
    with pytest.raises(ValueError, match="delay_seconds"):
        SimulatedChatGenerationClient(delay_seconds=-0.001)


@pytest.mark.asyncio
async def test_start_chat_returns_local_session_title_and_simulated_answer() -> (
    None
):
    client = SimulatedChatGenerationClient(delay_seconds=0)

    result = await client.start_chat("ローカル検証用の質問です")

    assert result.session_id.startswith("local-")
    assert UUID(result.session_id.removeprefix("local-")).version == 7
    assert "ローカル動作確認用" in result.answer
    assert result.answer.count("ローカル動作確認用") == 1
    assert '""' not in result.answer
    assert not any(line.startswith(" ") for line in result.answer.splitlines())


@pytest.mark.asyncio
async def test_continue_chat_keeps_session_and_returns_simulated_answer() -> None:
    client = SimulatedChatGenerationClient(delay_seconds=0)

    result = await client.continue_chat("local-session", "続きの質問")

    assert result.session_id == "local-session"
    assert "疑似回答" in result.answer
    assert result.answer.count("疑似回答") == 1
    assert '""' not in result.answer
    assert not any(line.startswith(" ") for line in result.answer.splitlines())
