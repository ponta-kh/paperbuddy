from pydantic import BaseModel, Field
import uuid

class ChatInitRequest(BaseModel):
    message: str = Field(..., description="チャットの初回メッセージ")

class ChatInitResponse(BaseModel):
    session_id: uuid.UUID = Field(..., description="セッションID")
    message: str = Field(..., description="アシスタントからの返答メッセージ")

class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="チャットメッセージ")

class ChatMessageResponse(BaseModel):
    message: str = Field(..., description="アシスタントからの返答メッセージ")
