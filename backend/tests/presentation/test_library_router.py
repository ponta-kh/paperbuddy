from fastapi.testclient import TestClient

from main import app
from src.application.use_cases.library.list_indexed_files.list_indexed_files_dto import (
    IndexedFileOutput,
    ListIndexedFilesOutput,
)
from src.dependencies.library_deps import get_list_indexed_files_use_case


class StubListIndexedFilesUseCase:
    async def execute(self) -> ListIndexedFilesOutput:
        return ListIndexedFilesOutput(
            files=(
                IndexedFileOutput(name="paper-a.pdf"),
                IndexedFileOutput(name="paper-b.pdf"),
            )
        )


def test_list_indexed_files_endpoint() -> None:
    app.dependency_overrides[get_list_indexed_files_use_case] = lambda: (
        StubListIndexedFilesUseCase()
    )
    client = TestClient(app)

    response = client.get(
        "/api/library/files",
        headers={"X-User-ID": "00000000-0000-0000-0000-000000000001"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "files": [{"name": "paper-a.pdf"}, {"name": "paper-b.pdf"}]
    }


def test_list_indexed_files_endpoint_rejects_missing_authentication() -> None:
    response = TestClient(app).get("/api/library/files")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_failed"
