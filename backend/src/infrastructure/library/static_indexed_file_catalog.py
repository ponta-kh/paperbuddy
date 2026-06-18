from src.application.ports.out.indexed_file_catalog_protocol import IndexedFile


class StaticIndexedFileCatalog:
    """ローカル動作確認用の固定インデックス済みファイルCatalog。"""

    def __init__(self, indexed_files: tuple[IndexedFile, ...] = ()) -> None:
        self._indexed_files = indexed_files

    async def list_indexed_files(self) -> tuple[IndexedFile, ...]:
        """生成時に渡された固定ファイル一覧を返す。"""

        return self._indexed_files
