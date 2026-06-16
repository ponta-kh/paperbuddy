from fastapi import Depends, FastAPI

from src.presentation.exception_handlers import register_exception_handlers
from src.presentation.request_id import get_request_id
from src.presentation.routers.chat_router import router as chat_router
from src.presentation.routers.health_router import router as health_router
from src.presentation.routers.library_router import router as library_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="PaperBuddy Backend",
        dependencies=[Depends(get_request_id)],
    )
    app.include_router(health_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(library_router, prefix="/api")
    register_exception_handlers(app)
    return app


app = create_app()
