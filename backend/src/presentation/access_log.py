import logging
from time import perf_counter
from uuid import UUID

from fastapi import FastAPI, Request

from src.dependencies.logging_config import clear_log_context, set_log_context
from src.presentation.request_id import get_request_id

logger = logging.getLogger(__name__)


def register_access_log_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def access_log_middleware(request: Request, call_next):
        request_id = get_request_id(request)
        set_log_context(request_id=request_id)
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = _elapsed_milliseconds(started_at)
            logger.exception(
                "HTTPリクエスト処理中に未処理例外が発生しました",
                extra=_access_log_fields(
                    request=request,
                    request_id=request_id,
                    status_code=500,
                    duration_ms=duration_ms,
                ),
            )
            clear_log_context()
            raise

        duration_ms = _elapsed_milliseconds(started_at)
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            "HTTPリクエストを処理しました",
            extra=_access_log_fields(
                request=request,
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=duration_ms,
            ),
        )
        clear_log_context()
        return response


def _elapsed_milliseconds(started_at: float) -> int:
    return round((perf_counter() - started_at) * 1000)


def _access_log_fields(
    *,
    request: Request,
    request_id: UUID,
    status_code: int,
    duration_ms: int,
) -> dict[str, object]:
    fields: dict[str, object] = {
        "event": "http_request",
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "request_id": str(request_id),
    }
    user_id = getattr(request.state, "user_id", None)
    if isinstance(user_id, UUID):
        fields["user_id"] = str(user_id)
    return fields
