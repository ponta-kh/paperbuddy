import io
import json
import logging
import sys
from collections.abc import Iterator

import pytest

from src.dependencies.logging_config import JsonLogFormatter, configure_logging


@pytest.fixture
def restore_logging() -> Iterator[None]:
    root_logger = logging.getLogger()
    handlers = root_logger.handlers[:]
    level = root_logger.level
    propagate_settings = {
        name: logging.getLogger(name).propagate
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access")
    }
    yield
    root_logger.handlers = handlers
    root_logger.setLevel(level)
    for name, propagate in propagate_settings.items():
        logging.getLogger(name).propagate = propagate


def test_json_log_formatter_outputs_structured_log() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="src.application.example",
        level=logging.INFO,
        pathname="example.py",
        lineno=10,
        msg="処理が完了しました",
        args=(),
        exc_info=None,
    )
    record.request_id = "019ecde4-0000-7000-8000-000000000001"
    record.user_id = "00000000-0000-0000-0000-000000000001"

    payload = json.loads(formatter.format(record))

    assert payload["timestamp"].endswith("Z")
    assert payload["level"] == "INFO"
    assert payload["logger"] == "src.application.example"
    assert payload["message"] == "処理が完了しました"
    assert payload["request_id"] == "019ecde4-0000-7000-8000-000000000001"
    assert payload["user_id"] == "00000000-0000-0000-0000-000000000001"


def test_json_log_formatter_outputs_exception() -> None:
    formatter = JsonLogFormatter()

    try:
        raise RuntimeError("外部サービス呼び出しに失敗しました")
    except RuntimeError:
        record = logging.getLogger("src.infrastructure.example").makeRecord(
            name="src.infrastructure.example",
            level=logging.ERROR,
            fn="example.py",
            lno=20,
            msg="保存に失敗しました",
            args=(),
            exc_info=sys.exc_info(),
            func=None,
            extra=None,
        )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "ERROR"
    assert payload["exception"]["type"] == "RuntimeError"
    assert payload["exception"]["message"] == "外部サービス呼び出しに失敗しました"
    assert "RuntimeError" in payload["exception"]["stack_trace"]


def test_configure_logging_writes_json_to_stream(
    restore_logging: None,
) -> None:
    stream = io.StringIO()
    configure_logging(level="DEBUG", stream=stream)

    logger = logging.getLogger("src.presentation.example")
    logger.debug(
        "リクエストを受け付けました",
        extra={"path": "/api/health"},
    )

    payload = json.loads(stream.getvalue())

    assert payload["level"] == "DEBUG"
    assert payload["logger"] == "src.presentation.example"
    assert payload["message"] == "リクエストを受け付けました"
    assert payload["path"] == "/api/health"


def test_configure_logging_falls_back_to_info_for_unknown_level(
    restore_logging: None,
) -> None:
    stream = io.StringIO()
    configure_logging(level="unknown", stream=stream)

    logging.getLogger("src.presentation.example").debug("出力されないログ")

    assert stream.getvalue() == ""
