import pytest
from pydantic import ValidationError

from src.dependencies.settings import (
    ChatGenerationMode,
    ChatInfrastructureMode,
    Settings,
)


def test_loads_aws_mode_settings() -> None:
    settings = Settings(
        aws_region="ap-northeast-1",
        dynamodb_chat_table_name="chat-table",
        dynamodb_library_table_name="library-table",
        bedrock_knowledge_base_id="knowledge-base-id",
        bedrock_model_arn="model-arn",
    )

    assert settings.chat_infrastructure_mode is ChatInfrastructureMode.AWS
    assert settings.chat_generation_mode is ChatGenerationMode.AWS
    assert settings.dynamodb_library_table_name == "library-table"
    assert settings.simulated_llm_delay_seconds == 2


def test_loads_local_mode_settings_without_bedrock() -> None:
    settings = Settings(
        chat_infrastructure_mode=ChatInfrastructureMode.LOCAL,
        aws_region="ap-northeast-1",
        dynamodb_chat_table_name="chat-table",
        dynamodb_library_table_name="library-table",
        dynamodb_endpoint_url="http://dynamodb-local:8000",
        simulated_llm_delay_seconds=0.5,
    )

    assert settings.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL
    assert settings.chat_generation_mode is ChatGenerationMode.LOCAL
    assert settings.dynamodb_library_table_name == "library-table"
    assert settings.simulated_llm_delay_seconds == 0.5


def test_loads_local_infrastructure_with_aws_chat_generation() -> None:
    settings = Settings(
        chat_infrastructure_mode=ChatInfrastructureMode.LOCAL,
        chat_generation_mode=ChatGenerationMode.AWS,
        aws_region="ap-northeast-1",
        dynamodb_chat_table_name="chat-table",
        dynamodb_library_table_name="library-table",
        dynamodb_endpoint_url="http://dynamodb-local:8000",
        bedrock_knowledge_base_id="knowledge-base-id",
        bedrock_model_arn="model-arn",
    )

    assert settings.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL
    assert settings.chat_generation_mode is ChatGenerationMode.AWS


def test_loads_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAT_INFRASTRUCTURE_MODE", "local")
    monkeypatch.setenv("CHAT_GENERATION_MODE", "aws")
    monkeypatch.setenv("AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv("DYNAMODB_CHAT_TABLE_NAME", "chat-table")
    monkeypatch.setenv("DYNAMODB_LIBRARY_TABLE_NAME", "library-table")
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", "http://dynamodb-local:8000")
    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "knowledge-base-id")
    monkeypatch.setenv("BEDROCK_MODEL_ARN", "model-arn")
    monkeypatch.setenv("SIMULATED_LLM_DELAY_SECONDS", "1.5")

    settings = Settings()

    assert settings.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL
    assert settings.chat_generation_mode is ChatGenerationMode.AWS
    assert settings.aws_region == "ap-northeast-1"
    assert settings.dynamodb_chat_table_name == "chat-table"
    assert settings.dynamodb_library_table_name == "library-table"
    assert settings.dynamodb_endpoint_url == "http://dynamodb-local:8000"
    assert settings.simulated_llm_delay_seconds == 1.5


@pytest.mark.parametrize(
    ("values", "message"),
    [
        (
            {
                "chat_generation_mode": "aws",
                "aws_region": "ap-northeast-1",
                "dynamodb_chat_table_name": "chat-table",
                "dynamodb_library_table_name": "library-table",
                "bedrock_model_arn": "model-arn",
            },
            "BEDROCK_KNOWLEDGE_BASE_ID",
        ),
        (
            {
                "chat_generation_mode": "aws",
                "aws_region": "ap-northeast-1",
                "dynamodb_chat_table_name": "chat-table",
                "dynamodb_library_table_name": "library-table",
                "bedrock_knowledge_base_id": "knowledge-base-id",
            },
            "BEDROCK_MODEL_ARN",
        ),
        (
            {
                "chat_infrastructure_mode": "local",
                "aws_region": "ap-northeast-1",
                "dynamodb_chat_table_name": "chat-table",
                "dynamodb_library_table_name": "library-table",
            },
            "DYNAMODB_ENDPOINT_URL",
        ),
    ],
)
def test_rejects_missing_mode_specific_settings(
    values: dict[str, str],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings.model_validate(values)


def test_rejects_negative_simulated_llm_delay() -> None:
    with pytest.raises(ValidationError, match="simulated_llm_delay_seconds"):
        Settings(
            chat_infrastructure_mode=ChatInfrastructureMode.LOCAL,
            aws_region="ap-northeast-1",
            dynamodb_chat_table_name="chat-table",
            dynamodb_library_table_name="library-table",
            dynamodb_endpoint_url="http://dynamodb-local:8000",
            simulated_llm_delay_seconds=-0.001,
        )


def test_rejects_unknown_chat_generation_mode() -> None:
    with pytest.raises(ValidationError, match="chat_generation_mode"):
        Settings(
            chat_infrastructure_mode=ChatInfrastructureMode.LOCAL,
            chat_generation_mode="unknown",
            aws_region="ap-northeast-1",
            dynamodb_chat_table_name="chat-table",
            dynamodb_library_table_name="library-table",
            dynamodb_endpoint_url="http://dynamodb-local:8000",
        )
