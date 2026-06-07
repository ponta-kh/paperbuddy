from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.application.exceptions import (
    ChatContinuationExpiredError,
    RepositoryNotFoundError,
)
from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationUnavailableError,
    InvalidChatGenerationResponseError,
)
from src.domain.exceptions.chat_exception import InvalidPromptError, PromptTooLongError
from src.domain.repositories.chat_command_repository_protocol import (
    ChatConflictError,
    ChatNotFoundError,
    ChatSaveError,
)
from src.presentation.auth import AuthenticationError


def _response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"code": code, "message": message}
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ChatNotFoundError)
    async def chat_not_found_handler(_: Request, __: ChatNotFoundError) -> JSONResponse:
        return _response(
            status.HTTP_404_NOT_FOUND,
            "chat_not_found",
            "指定されたチャットは存在しません",
        )

    @app.exception_handler(ChatConflictError)
    async def chat_conflict_handler(_: Request, __: ChatConflictError) -> JSONResponse:
        return _response(
            status.HTTP_409_CONFLICT,
            "chat_conflict",
            "チャットが更新されたため、再度お試しください",
        )

    @app.exception_handler(ChatContinuationExpiredError)
    async def chat_continuation_expired_handler(
        _: Request, __: ChatContinuationExpiredError
    ) -> JSONResponse:
        return _response(
            status.HTTP_409_CONFLICT,
            "chat_continuation_expired",
            "このチャットでは会話を継続できません",
        )

    @app.exception_handler(RepositoryNotFoundError)
    async def repository_not_found_handler(
        _: Request, __: RepositoryNotFoundError
    ) -> JSONResponse:
        return _response(
            status.HTTP_404_NOT_FOUND,
            "chat_not_found",
            "指定されたチャットは存在しません",
        )

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
            "チャットの回答を生成できませんでした",
        )

    @app.exception_handler(InvalidChatGenerationResponseError)
    async def invalid_generation_response_handler(
        _: Request, __: InvalidChatGenerationResponseError
    ) -> JSONResponse:
        return _response(
            status.HTTP_502_BAD_GATEWAY,
            "invalid_chat_generation_response",
            "チャットの回答を生成できませんでした",
        )

    @app.exception_handler(ChatSaveError)
    async def chat_save_error_handler(_: Request, __: ChatSaveError) -> JSONResponse:
        return _response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "chat_save_failed",
            "チャットを保存できませんでした",
        )
