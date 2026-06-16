from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ListIndexedFilesInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    request_id: UUID


@dataclass(frozen=True, slots=True)
class IndexedFileOutput:
    source_id: UUID
    s3_key: str
    name: str
    category: str
    status: str
    s3_uploaded_at: datetime
    rag_indexed_at: datetime | None


@dataclass(frozen=True, slots=True)
class ListIndexedFilesOutput:
    files: tuple[IndexedFileOutput, ...]
