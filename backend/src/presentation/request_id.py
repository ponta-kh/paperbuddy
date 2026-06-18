from uuid import UUID, uuid7

from fastapi import Request

from src.dependencies.logging_config import set_log_context


def get_request_id(request: Request) -> UUID:
    """HTTPリクエスト単位のUUID v7リクエストIDを返す。"""

    current = getattr(request.state, "request_id", None)
    if isinstance(current, UUID):
        set_log_context(request_id=current)
        return current

    # グローバル依存関係とRouter引数のどちらから参照しても、
    # 1つのHTTPリクエストでは同じIDを使う。
    request_id = uuid7()
    request.state.request_id = request_id
    set_log_context(request_id=request_id)
    return request_id
