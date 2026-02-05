"""Document-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Schema for document upload metadata."""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")


class DocumentChunkResponse(BaseModel):
    """Schema for a document chunk response."""

    id: int
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    page_number: Optional[int] = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: int
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response."""

    documents: list[DocumentResponse]
    total: int
    page: int = 1
    page_size: int = 20


class DocumentDetailResponse(BaseModel):
    """Schema for detailed document response with chunks."""

    id: int
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    has_raw_text: bool = False
    has_file_bytes: bool = False
    chunks: list[DocumentChunkResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Custom validation to handle raw_text and file_bytes flags."""
        if hasattr(obj, "raw_text"):
            kwargs.setdefault("context", {})
        data = {
            "id": obj.id,
            "filename": obj.filename,
            "original_filename": obj.original_filename,
            "content_type": obj.content_type,
            "file_size": obj.file_size,
            "status": obj.status,
            "error_message": obj.error_message,
            "chunk_count": obj.chunk_count,
            "has_raw_text": obj.raw_text is not None if hasattr(obj, "raw_text") else False,
            "has_file_bytes": obj.file_bytes is not None if hasattr(obj, "file_bytes") else False,
            "chunks": [DocumentChunkResponse.model_validate(c) for c in obj.chunks] if hasattr(obj, "chunks") and obj.chunks else [],
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return cls(**data)
