from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.application.ports.input.chat.continue_chat_protocol import ContinueChatProtocol
from src.application.ports.input.chat.delete_chat_protocol import DeleteChatProtocol
from src.application.ports.input.chat.list_chat_messages_protocol import (
    ListChatMessagesProtocol,
)
from src.application.ports.input.chat.list_chats_protocol import ListChatsProtocol
from src.application.ports.input.chat.rename_chat_protocol import RenameChatProtocol
from src.application.ports.input.chat.start_chat_protocol import (
    StartChatProtocol,
)
from src.application.use_cases.chat.continue_chat.continue_chat_dto import (
    ContinueChatInput,
)
from src.application.use_cases.chat.delete_chat.delete_chat_dto import DeleteChatInput
from src.application.use_cases.chat.list_chat_messages.list_chat_messages_dto import (
    ListChatMessagesInput,
)
from src.application.use_cases.chat.list_chats.list_chats_dto import ListChatsInput
from src.application.use_cases.chat.rename_chat.rename_chat_dto import RenameChatInput
from src.application.use_cases.chat.start_chat.start_chat_dto import StartChatInput
from src.dependencies.chat_deps import (
    get_continue_chat_use_case,
    get_delete_chat_use_case,
    get_list_chat_messages_use_case,
    get_list_chats_use_case,
    get_rename_chat_use_case,
    get_start_chat_use_case,
)
from src.presentation.auth import AuthenticatedUser, get_authenticated_user
from src.presentation.request_id import get_request_id
from src.presentation.schemas.chat_schema import (
    ChatMessageResponse,
    ChatSummaryResponse,
    ContinueChatRequest,
    ContinueChatResponse,
    ListChatMessagesResponse,
    ListChatsResponse,
    RenameChatRequest,
    RenameChatResponse,
    StartChatRequest,
    StartChatResponse,
)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.patch("/{chat_id}", response_model=RenameChatResponse)
async def rename_chat(
    chat_id: UUID,
    request: RenameChatRequest,
    request_id: Annotated[UUID, Depends(get_request_id)],
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[RenameChatProtocol, Depends(get_rename_chat_use_case)],
) -> RenameChatResponse:
    output = await use_case.execute(
        RenameChatInput(
            user_id=user.user_id,
            chat_id=chat_id,
            title=request.title,
            request_id=request_id,
        )
    )
    return RenameChatResponse(chat_id=output.chat_id, title=output.title)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    request_id: Annotated[UUID, Depends(get_request_id)],
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[DeleteChatProtocol, Depends(get_delete_chat_use_case)],
) -> None:
    await use_case.execute(
        DeleteChatInput(
            chat_id=chat_id,
            user_id=user.user_id,
            request_id=request_id,
        )
    )


@router.get("", response_model=ListChatsResponse)
async def list_chats(
    request_id: Annotated[UUID, Depends(get_request_id)],
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[ListChatsProtocol, Depends(get_list_chats_use_case)],
) -> ListChatsResponse:
    output = await use_case.execute(
        ListChatsInput(user_id=user.user_id, request_id=request_id)
    )
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
    chat_id: UUID,
    request_id: Annotated[UUID, Depends(get_request_id)],
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[
        ListChatMessagesProtocol, Depends(get_list_chat_messages_use_case)
    ],
) -> ListChatMessagesResponse:
    output = await use_case.execute(
        ListChatMessagesInput(
            user_id=user.user_id,
            chat_id=chat_id,
            request_id=request_id,
        )
    )
    return ListChatMessagesResponse(
        chat_id=output.chat_id,
        messages=[
            ChatMessageResponse(
                request_id=message.request_id,
                sender=message.sender,
                content=message.content,
                sent_at=message.sent_at,
            )
            for message in output.messages
        ],
    )


@router.post("/{chat_id}/messages", response_model=ContinueChatResponse)
async def continue_chat(
    chat_id: UUID,
    request: ContinueChatRequest,
    request_id: Annotated[UUID, Depends(get_request_id)],
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[ContinueChatProtocol, Depends(get_continue_chat_use_case)],
) -> ContinueChatResponse:
    output = await use_case.execute(
        ContinueChatInput(
            user_id=user.user_id,
            chat_id=chat_id,
            prompt=request.prompt,
            request_id=request_id,
        )
    )
    return ContinueChatResponse(
        chat_id=output.chat_id,
        answer=output.answer,
        title=output.title,
        last_updated_at=output.last_updated_at,
    )


@router.post("", response_model=StartChatResponse, status_code=status.HTTP_201_CREATED)
async def start_chat(
    request: StartChatRequest,
    request_id: Annotated[UUID, Depends(get_request_id)],
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[StartChatProtocol, Depends(get_start_chat_use_case)],
) -> StartChatResponse:
    output = await use_case.execute(
        StartChatInput(
            user_id=user.user_id,
            prompt=request.prompt,
            request_id=request_id,
        )
    )
    return StartChatResponse(
        chat_id=output.chat_id,
        answer=output.answer,
        title=output.title,
        last_updated_at=output.last_updated_at,
    )
