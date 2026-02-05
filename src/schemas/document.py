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
    chunks: list[DocumentChunkResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
