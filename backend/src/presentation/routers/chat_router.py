from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.application.use_cases.chat.list_chat_messages.list_chat_messages import (
    ListChatMessagesUseCase,
)
from src.application.use_cases.chat.list_chat_messages.list_chat_messages_dto import (
    ListChatMessagesInput,
)
from src.application.use_cases.chat.list_chats.list_chats import ListChatsUseCase
from src.application.use_cases.chat.list_chats.list_chats_dto import ListChatsInput
from src.application.use_cases.chat.start_chat.start_chat import StartChatUseCase
from src.application.use_cases.chat.start_chat.start_chat_dto import StartChatInput
from src.dependencies.chat_deps import (
    get_list_chat_messages_use_case,
    get_list_chats_use_case,
    get_start_chat_use_case,
)
from src.presentation.auth import AuthenticatedUser, get_authenticated_user
from src.presentation.schemas.chat_schema import (
    ChatMessageResponse,
    ChatSummaryResponse,
    ListChatMessagesResponse,
    ListChatsResponse,
    StartChatRequest,
    StartChatResponse,
)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=ListChatsResponse)
async def list_chats(
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[ListChatsUseCase, Depends(get_list_chats_use_case)],
) -> ListChatsResponse:
    output = await use_case.execute(ListChatsInput(user_id=user.user_id))
    return ListChatsResponse(
        chats=[
            ChatSummaryResponse(
                chat_id=chat.chat_id,
                title=chat.title,
                created_at=chat.created_at,
                last_updated_at=chat.last_updated_at,
            )
            for chat in output.chats
        ]
    )


@router.get("/{chat_id}/messages", response_model=ListChatMessagesResponse)
async def list_chat_messages(
    chat_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[
        ListChatMessagesUseCase, Depends(get_list_chat_messages_use_case)
    ],
) -> ListChatMessagesResponse:
    output = await use_case.execute(
        ListChatMessagesInput(user_id=user.user_id, chat_id=chat_id)
    )
    return ListChatMessagesResponse(
        chat_id=output.chat_id,
        messages=[
            ChatMessageResponse(
                turn_id=message.turn_id,
                sender=message.sender,
                content=message.content,
                sent_at=message.sent_at,
            )
            for message in output.messages
        ],
    )


@router.post("", response_model=StartChatResponse, status_code=status.HTTP_201_CREATED)
async def start_chat(
    request: StartChatRequest,
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[StartChatUseCase, Depends(get_start_chat_use_case)],
) -> StartChatResponse:
    output = await use_case.execute(
        StartChatInput(user_id=user.user_id, prompt=request.prompt)
    )
    return StartChatResponse(
        chat_id=output.chat_id, answer=output.answer, title=output.title
    )
