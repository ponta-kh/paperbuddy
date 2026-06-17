from uuid import UUID

import pytest

from src.infrastructure.llm.simulated_chat_generation_client import (
    SimulatedChatGenerationClient,
)


def test_rejects_negative_delay() -> None:
    with pytest.raises(ValueError, match="delay_seconds"):
        SimulatedChatGenerationClient(delay_seconds=-0.001)


@pytest.mark.asyncio
async def test_start_chat_returns_local_session_title_and_simulated_answer() -> None:
    client = SimulatedChatGenerationClient(delay_seconds=0)

    result = await client.start_chat("ローカル検証用の質問です")

    assert result.session_id.startswith("local-")
    assert UUID(result.session_id.removeprefix("local-")).version == 7
    assert "ローカル動作確認用" in result.answer
    assert len(result.citations) == 2
    assert result.citations[0].text == "これはローカル動作確認用の疑似回答です。"
    assert result.citations[0].span_start == 0
    assert result.citations[0].span_end == 20
    assert len(result.citations[0].sources) == 1
    assert result.citations[0].sources[0].location_type == "S3"
    assert result.citations[0].sources[0].uri == (
        "s3://paperbuddy-local-rag-sources/sample-paper.pdf"
    )
    assert result.citations[0].sources[0].metadata["title"] == (
        "PaperBuddy ローカル検証用サンプル論文"
    )
    assert result.citations[0].sources[0].metadata["page"] == 1
    assert result.answer.count("ローカル動作確認用") == 1
    assert '""' not in result.answer
    assert not any(line.startswith(" ") for line in result.answer.splitlines())


@pytest.mark.asyncio
async def test_continue_chat_keeps_session_and_returns_simulated_answer() -> None:
    client = SimulatedChatGenerationClient(delay_seconds=0)

    result = await client.continue_chat("local-session", "続きの質問")

    assert result.session_id == "local-session"
    assert "疑似回答" in result.answer
    assert len(result.citations) == 2
    assert result.citations[1].sources[0].metadata["title"] == (
        "チャット動作確認ガイド"
    )
    assert result.citations[1].sources[0].metadata["page"] == 4
    assert result.answer.count("疑似回答") == 1
    assert '""' not in result.answer
    assert not any(line.startswith(" ") for line in result.answer.splitlines())
