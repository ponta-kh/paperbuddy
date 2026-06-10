from pydantic import BaseModel, Field


class IndexedFileResponse(BaseModel):
    name: str = Field(description="RAGへ取り込み済みのファイル名")


class ListIndexedFilesResponse(BaseModel):
    files: list[IndexedFileResponse]
