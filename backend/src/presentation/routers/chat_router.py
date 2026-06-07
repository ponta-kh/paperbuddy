from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.application.use_cases.chat.start_chat.start_chat import StartChatUseCase
from src.application.use_cases.chat.start_chat.start_chat_dto import StartChatInput
from src.dependencies.chat_deps import get_start_chat_use_case
from src.presentation.auth import AuthenticatedUser, get_authenticated_user
from src.presentation.schemas.chat_schema import StartChatRequest, StartChatResponse

router = APIRouter(prefix="/chats", tags=["chats"])


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
