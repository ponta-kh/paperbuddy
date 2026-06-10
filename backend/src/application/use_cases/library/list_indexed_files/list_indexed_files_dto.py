from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IndexedFileOutput:
    name: str


@dataclass(frozen=True, slots=True)
class ListIndexedFilesOutput:
    files: tuple[IndexedFileOutput, ...]
