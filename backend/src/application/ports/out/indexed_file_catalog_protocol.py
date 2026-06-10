from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class IndexedFile:
    source_id: UUID
    s3_key: str
    name: str
    category: str
    status: str
    s3_uploaded_at: datetime
    rag_indexed_at: datetime | None


class IndexedFileCatalogProtocol(Protocol):
    async def list_indexed_files(self) -> tuple[IndexedFile, ...]: ...
