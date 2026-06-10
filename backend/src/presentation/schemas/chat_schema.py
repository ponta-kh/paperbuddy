from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StartChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(description="チャットを開始する最初のプロンプト")


class StartChatResponse(BaseModel):
    chat_id: UUID
    answer: str
    title: str


class ContinueChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(description="既存チャットへ追加するプロンプト")


class ContinueChatResponse(BaseModel):
    chat_id: UUID
    answer: str
    title: str


class RenameChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="変更後のチャットタイトル")


class RenameChatResponse(BaseModel):
    chat_id: UUID
    title: str


class ChatSummaryResponse(BaseModel):
    chat_id: UUID
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
    chat_id: UUID
    messages: list[ChatMessageResponse]


class ErrorResponse(BaseModel):
    code: str
    message: str
