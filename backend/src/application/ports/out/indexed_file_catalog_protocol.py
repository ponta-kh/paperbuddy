from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class IndexedFile:
    name: str


class IndexedFileCatalogProtocol(Protocol):
    async def list_indexed_files(self) -> tuple[IndexedFile, ...]: ...
