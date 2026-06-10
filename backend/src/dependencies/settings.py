from enum import StrEnum
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatInfrastructureMode(StrEnum):
    AWS = "aws"
    LOCAL = "local"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    chat_infrastructure_mode: ChatInfrastructureMode = ChatInfrastructureMode.AWS
    aws_region: str = Field(default="", min_length=1)
    dynamodb_chat_table_name: str = Field(default="", min_length=1)
    dynamodb_endpoint_url: str | None = None
    bedrock_knowledge_base_id: str | None = None
    bedrock_model_arn: str | None = None
    simulated_llm_delay_seconds: float = Field(default=2, ge=0)

    @model_validator(mode="after")
    def validate_mode_specific_settings(self) -> "Settings":
        if self.chat_infrastructure_mode is ChatInfrastructureMode.LOCAL:
            if not self.dynamodb_endpoint_url:
                raise ValueError("DYNAMODB_ENDPOINT_URL is required in local mode")
            return self

        missing = [
            name
            for name, value in (
                ("BEDROCK_KNOWLEDGE_BASE_ID", self.bedrock_knowledge_base_id),
                ("BEDROCK_MODEL_ARN", self.bedrock_model_arn),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"{', '.join(missing)} is required in aws mode")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
