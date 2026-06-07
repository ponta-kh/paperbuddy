from pydantic import BaseModel, ConfigDict, Field


class StartChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(description="チャットを開始する最初のプロンプト")


class StartChatResponse(BaseModel):
    chat_id: str
    answer: str
    title: str


class ErrorResponse(BaseModel):
    code: str
    message: str
