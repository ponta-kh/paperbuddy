from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IndexedFileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: UUID = Field(description="データソース識別子")
    s3_key: str = Field(description="S3オブジェクトキー")
    name: str = Field(description="RAGへ取り込み済みのファイル名")
    category: str = Field(description="書類分類")
    status: str = Field(description="取り込みステータス")
    s3_uploaded_at: datetime = Field(description="S3アップロード日時")
    rag_indexed_at: datetime | None = Field(description="RAG組み込み日時")


class ListIndexedFilesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[IndexedFileResponse]
