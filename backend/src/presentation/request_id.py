from uuid import UUID, uuid7

from fastapi import Request


def get_request_id(request: Request) -> UUID:
    current = getattr(request.state, "request_id", None)
    if isinstance(current, UUID):
        return current

    # グローバル依存関係とRouter引数のどちらから参照しても、
    # 1つのHTTPリクエストでは同じIDを使う。
    request_id = uuid7()
    request.state.request_id = request_id
    return request_id
