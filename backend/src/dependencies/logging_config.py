import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any, TextIO

_request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)
_user_id_context: ContextVar[str | None] = ContextVar("user_id", default=None)

_RESERVED_LOG_RECORD_ATTRIBUTES = frozenset(
    logging.LogRecord(
        name="",
        level=0,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__
) | {"asctime", "message"}


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(_current_context_fields())
        payload.update(_extract_extra_fields(record))

        if record.exc_info:
            payload["exception"] = _format_exception(record, self.formatException)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(
    *,
    level: str = "INFO",
    stream: TextIO | None = None,
) -> None:
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(_resolve_log_level(level))

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(_resolve_log_level(level))


def set_log_context(
    *,
    request_id: object | None = None,
    user_id: object | None = None,
) -> None:
    if request_id is not None:
        _request_id_context.set(str(request_id))
    if user_id is not None:
        _user_id_context.set(str(user_id))


def clear_log_context() -> None:
    _request_id_context.set(None)
    _user_id_context.set(None)


def _resolve_log_level(level: str) -> int:
    resolved_level = logging.getLevelName(level.upper())
    if isinstance(resolved_level, int):
        return resolved_level
    return logging.INFO


def _extract_extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in _RESERVED_LOG_RECORD_ATTRIBUTES and not key.startswith("_")
    }


def _current_context_fields() -> dict[str, str]:
    fields: dict[str, str] = {}
    request_id = _request_id_context.get()
    user_id = _user_id_context.get()
    if request_id:
        fields["request_id"] = request_id
    if user_id:
        fields["user_id"] = user_id
    return fields


def _format_exception(
    record: logging.LogRecord,
    format_exception: Any,
) -> dict[str, str]:
    exception_type, exception, traceback = record.exc_info or (None, None, None)
    return {
        "type": _exception_type_name(exception_type),
        "message": str(exception) if exception else "",
        "stack_trace": format_exception((exception_type, exception, traceback)),
    }


def _exception_type_name(
    exception_type: type[BaseException] | None,
) -> str:
    return exception_type.__name__ if exception_type else ""
