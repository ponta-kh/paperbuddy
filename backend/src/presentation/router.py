from fastapi import APIRouter, Path
import uuid
from src.presentation.schema import ChatInitRequest, ChatInitResponse, ChatMessageRequest, ChatMessageResponse

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("", response_model=ChatInitResponse, summary="チャットの初回コメント送付")
async def create_chat(request: ChatInitRequest) -> ChatInitResponse:
    """
    初回チャットのセッションを開始し、メッセージを送付します。
    """
    # TODO: 初回チャット処理のロジックを実装する
    mock_session_id = uuid.uuid4()
    return ChatInitResponse(
        session_id=mock_session_id,
        message=f"Mock response for first message: {request.message}"
    )

@router.post("/{session_id}", response_model=ChatMessageResponse, summary="2回目以降のコメント送付")
async def send_message(
    session_id: uuid.UUID = Path(..., description="チャットのセッションID"),
    request: ChatMessageRequest = None
) -> ChatMessageResponse:
    """
    既存のセッションIDを指定して、2回目以降のメッセージを送付します。
    """
    # TODO: 2回目以降のチャット処理のロジックを実装する
    return ChatMessageResponse(
        message=f"Mock response for session {session_id}: {request.message}"
    )
