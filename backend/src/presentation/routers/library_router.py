from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.application.ports.input.library.list_indexed_files_protocol import (
    ListIndexedFilesProtocol,
)
from src.application.use_cases.library.list_indexed_files.list_indexed_files_dto import (
    ListIndexedFilesInput,
)
from src.dependencies.library_deps import get_list_indexed_files_use_case
from src.presentation.auth import AuthenticatedUser, get_authenticated_user
from src.presentation.request_id import get_request_id
from src.presentation.schemas.library_schema import (
    IndexedFileResponse,
    ListIndexedFilesResponse,
)

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/files", response_model=ListIndexedFilesResponse)
async def list_indexed_files(
    request_id: Annotated[UUID, Depends(get_request_id)],
    _: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    use_case: Annotated[
        ListIndexedFilesProtocol, Depends(get_list_indexed_files_use_case)
    ],
) -> ListIndexedFilesResponse:
    output = await use_case.execute(ListIndexedFilesInput(request_id=request_id))
    return ListIndexedFilesResponse(
        files=[
            IndexedFileResponse(
                source_id=file.source_id,
                s3_key=file.s3_key,
                name=file.name,
                category=file.category,
                status=file.status,
                s3_uploaded_at=file.s3_uploaded_at,
                rag_indexed_at=file.rag_indexed_at,
            )
            for file in output.files
        ]
    )
