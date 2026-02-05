"""Document management API endpoints."""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import get_settings
from src.database import get_db
from src.models.document import Document, DocumentChunk
from src.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from src.services.ingestion import IngestionService

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List all documents with pagination."""
    offset = (page - 1) * page_size

    query = select(Document).order_by(Document.created_at.desc())
    if status_filter:
        query = query.where(Document.status == status_filter)

    # Get total count
    count_query = select(func.count(Document.id))
    if status_filter:
        count_query = count_query.where(Document.status == status_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload and process a new document."""
    # Validate file type
    allowed_types = ["application/pdf", "text/plain", "text/markdown"]
    content_type = file.content_type or "application/octet-stream"

    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}. Allowed: {allowed_types}",
        )

    # Read file bytes
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Check file size
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}"

    # Create document record
    document = Document(
        filename=unique_filename,
        original_filename=file.filename or "document",
        content_type=content_type,
        file_size=file_size,
        file_bytes=file_bytes if settings.store_raw_files else None,
        status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Process document in background
    ingestion_service = IngestionService()
    background_tasks.add_task(
        ingestion_service.process_document_from_bytes,
        document.id,
        file_bytes,
        content_type,
    )

    return DocumentResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: int,
    include_chunks: bool = False,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """Get a document by ID."""
    query = select(Document).where(Document.id == document_id)
    if include_chunks:
        query = query.options(selectinload(Document.chunks))

    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    return DocumentDetailResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document and its chunks."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Delete from database (cascades to chunks)
    await db.delete(document)
    await db.commit()


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Reprocess a document (re-chunk and re-embed)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    if not document.raw_text and not document.file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No stored content available for reprocessing",
        )

    # Reset status
    document.status = "pending"
    document.error_message = None
    await db.commit()

    # Process document in background
    ingestion_service = IngestionService()
    background_tasks.add_task(ingestion_service.reprocess_document, document.id)

    await db.refresh(document)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/raw")
async def get_document_raw_text(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the raw extracted text of a document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    return {
        "document_id": document.id,
        "filename": document.original_filename,
        "raw_text": document.raw_text,
        "has_file_bytes": document.file_bytes is not None,
    }
