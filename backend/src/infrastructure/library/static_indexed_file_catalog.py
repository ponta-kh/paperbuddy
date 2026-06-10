from src.application.ports.out.indexed_file_catalog_protocol import IndexedFile


class StaticIndexedFileCatalog:
    def __init__(self, indexed_files: tuple[IndexedFile, ...] = ()) -> None:
        self._indexed_files = indexed_files

    async def list_indexed_files(self) -> tuple[IndexedFile, ...]:
        return self._indexed_files
