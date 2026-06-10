from typing import Annotated

from fastapi import APIRouter, Depends

from src.application.ports.input.library.list_indexed_files_protocol import (
    ListIndexedFilesProtocol,
)
from src.dependencies.library_deps import get_list_indexed_files_use_case
from src.presentation.auth import AuthenticatedUser, get_authenticated_user
from src.presentation.schemas.library_schema import (
    IndexedFileResponse,
    ListIndexedFilesResponse,
)

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/files", response_model=ListIndexedFilesResponse)
async def list_indexed_files(
    _: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[
        ListIndexedFilesProtocol, Depends(get_list_indexed_files_use_case)
    ],
) -> ListIndexedFilesResponse:
    output = await use_case.execute()
    return ListIndexedFilesResponse(
        files=[IndexedFileResponse(name=file.name) for file in output.files]
    )
