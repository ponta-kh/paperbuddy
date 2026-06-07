from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StartChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(description="チャットを開始する最初のプロンプト")


class StartChatResponse(BaseModel):
    chat_id: str
    answer: str
    title: str


class ChatSummaryResponse(BaseModel):
    chat_id: str
    title: str
    created_at: datetime
    last_updated_at: datetime


class ListChatsResponse(BaseModel):
    chats: list[ChatSummaryResponse]


class ChatMessageResponse(BaseModel):
    turn_id: UUID
    sender: str
    content: str
    sent_at: datetime


class ListChatMessagesResponse(BaseModel):
    chat_id: str
    messages: list[ChatMessageResponse]


class ErrorResponse(BaseModel):
    code: str
    message: str
