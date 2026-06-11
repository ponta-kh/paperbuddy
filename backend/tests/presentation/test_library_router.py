from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from main import app
from src.application.use_cases.library.list_indexed_files.list_indexed_files_dto import (
    IndexedFileOutput,
    ListIndexedFilesOutput,
)
from src.dependencies.library_deps import get_list_indexed_files_use_case
from src.presentation.auth import AuthenticatedUser, get_authenticated_user

USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class StubListIndexedFilesUseCase:
    async def execute(self) -> ListIndexedFilesOutput:
        return ListIndexedFilesOutput(
            files=(
                IndexedFileOutput(
                    source_id=UUID("00000000-0000-0000-0000-000000000001"),
                    s3_key="papers/a.pdf",
                    name="paper-a.pdf",
                    category="LLM",
                    status="indexed",
                    s3_uploaded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    rag_indexed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                ),
                IndexedFileOutput(
                    source_id=UUID("00000000-0000-0000-0000-000000000002"),
                    s3_key="papers/b.pdf",
                    name="paper-b.pdf",
                    category="経済",
                    status="processing",
                    s3_uploaded_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                    rag_indexed_at=None,
                ),
            )
        )


def test_list_indexed_files_endpoint() -> None:
    app.dependency_overrides[get_list_indexed_files_use_case] = lambda: (
        StubListIndexedFilesUseCase()
    )
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=USER_ID
    )
    client = TestClient(app)

    response = client.get(
        "/api/library/files",
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "files": [
            {
                "source_id": "00000000-0000-0000-0000-000000000001",
                "s3_key": "papers/a.pdf",
                "name": "paper-a.pdf",
                "category": "LLM",
                "status": "indexed",
                "s3_uploaded_at": "2026-01-01T00:00:00Z",
                "rag_indexed_at": "2026-01-02T00:00:00Z",
            },
            {
                "source_id": "00000000-0000-0000-0000-000000000002",
                "s3_key": "papers/b.pdf",
                "name": "paper-b.pdf",
                "category": "経済",
                "status": "processing",
                "s3_uploaded_at": "2026-01-03T00:00:00Z",
                "rag_indexed_at": None,
            },
        ]
    }


def test_list_indexed_files_endpoint_rejects_missing_authentication() -> None:
    response = TestClient(app).get("/api/library/files")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_failed"
