from enum import StrEnum
from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatInfrastructureMode(StrEnum):
    """チャット永続化基盤の実行モード。"""

    AWS = "aws"
    LOCAL = "local"


class ChatGenerationMode(StrEnum):
    """チャット回答生成の実行モード。"""

    AWS = "aws"
    LOCAL = "local"


class Settings(BaseSettings):
    """環境変数から読み込むアプリケーション設定。"""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
        validate_default=True,
    )

    chat_infrastructure_mode: ChatInfrastructureMode = ChatInfrastructureMode.AWS
    chat_generation_mode: ChatGenerationMode | None = None
    aws_region: str = Field(default="", min_length=1)
    dynamodb_chat_table_name: str = Field(default="", min_length=1)
    dynamodb_library_table_name: str = Field(default="", min_length=1)
    dynamodb_endpoint_url: str | None = None
    bedrock_knowledge_base_id: str | None = None
    bedrock_generation_model_identifier: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "bedrock_generation_model_identifier",
            "BEDROCK_GENERATION_MODEL_IDENTIFIER",
            "BEDROCK_MODEL_ARN",
            "bedrock_model_arn",
        ),
    )
    cognito_user_pool_id: str | None = None
    cognito_user_pool_client_id: str | None = None
    simulated_llm_delay_seconds: float = Field(default=2, ge=0)

    @property
    def is_local_mode(self) -> bool:
        """チャット永続化基盤がローカル実行か判定する。"""

        return self.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL

    @property
    def uses_local_chat_generation(self) -> bool:
        """チャット回答生成がローカル疑似生成か判定する。"""

        return self.chat_generation_mode is ChatGenerationMode.LOCAL

    @model_validator(mode="after")
    def validate_mode_specific_settings(self) -> "Settings":
        """実行モードごとに必須設定が揃っていることを検証する。"""

        if self.chat_generation_mode is None:
            self.chat_generation_mode = (
                ChatGenerationMode.LOCAL
                if self.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL
                else ChatGenerationMode.AWS
            )

        if self.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL:
            if not self.dynamodb_endpoint_url:
                raise ValueError("DYNAMODB_ENDPOINT_URL is required in local mode")

        if self.chat_generation_mode is ChatGenerationMode.LOCAL:
            return self

        missing = [
            name
            for name, value in (
                ("BEDROCK_KNOWLEDGE_BASE_ID", self.bedrock_knowledge_base_id),
                (
                    "BEDROCK_GENERATION_MODEL_IDENTIFIER",
                    self.bedrock_generation_model_identifier,
                ),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"{', '.join(missing)} is required in aws mode")
        return self


@lru_cache
def get_settings() -> Settings:
    """アプリケーション設定を返すDIファクトリ。"""

    return Settings()
