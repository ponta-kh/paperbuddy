from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationUnavailableError,
    InvalidChatGenerationResponseError,
)
from src.domain.exceptions.chat_exception import InvalidPromptError, PromptTooLongError
from src.domain.repositories.chat_command_repository_protocol import ChatSaveError
from src.presentation.auth import AuthenticationError


def _response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"code": code, "message": message}
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        _: Request, __: AuthenticationError
    ) -> JSONResponse:
        return _response(
            status.HTTP_401_UNAUTHORIZED, "authentication_failed", "認証に失敗しました"
        )

    @app.exception_handler(InvalidPromptError)
    async def invalid_prompt_handler(
        _: Request, __: InvalidPromptError
    ) -> JSONResponse:
        return _response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "invalid_prompt",
            "プロンプトを入力してください",
        )

    @app.exception_handler(PromptTooLongError)
    async def prompt_too_long_handler(
        _: Request, __: PromptTooLongError
    ) -> JSONResponse:
        return _response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "prompt_too_long",
            "プロンプトは1000文字以内で入力してください",
        )

    @app.exception_handler(ChatGenerationUnavailableError)
    async def generation_unavailable_handler(
        _: Request, __: ChatGenerationUnavailableError
    ) -> JSONResponse:
        return _response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "chat_generation_unavailable",
            "チャットを開始できませんでした",
        )

    @app.exception_handler(InvalidChatGenerationResponseError)
    async def invalid_generation_response_handler(
        _: Request, __: InvalidChatGenerationResponseError
    ) -> JSONResponse:
        return _response(
            status.HTTP_502_BAD_GATEWAY,
            "invalid_chat_generation_response",
            "チャットを開始できませんでした",
        )

    @app.exception_handler(ChatSaveError)
    async def chat_save_error_handler(_: Request, __: ChatSaveError) -> JSONResponse:
        return _response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "chat_save_failed",
            "チャットを保存できませんでした",
        )
