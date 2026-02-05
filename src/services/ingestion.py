"""Document ingestion service - parsing, chunking, and embedding with pgvector."""

import io
import logging
import re
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy import select, delete

from src.config import get_settings
from src.database import get_db_context
from src.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()


class IngestionService:
    """Service for ingesting and processing documents into pgvector."""

    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def process_document(self, document_id: int) -> None:
        """Process a document: parse, chunk, embed, and store in Postgres."""
        async with get_db_context() as db:
            # Get document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return

            try:
                document.status = "processing"
                await db.commit()

                # Parse document content from stored bytes or file
                content = await self._parse_document(document)

                # Store raw text
                document.raw_text = content

                # Delete existing chunks if reprocessing
                await db.execute(
                    delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
                )

                # Chunk the content
                chunks = self._chunk_text(content, document.original_filename)

                if not chunks:
                    document.status = "completed"
                    document.chunk_count = 0
                    await db.commit()
                    return

                # Generate embeddings
                embeddings = await self._generate_embeddings([c["content"] for c in chunks])

                # Store chunks with embeddings
                db_chunks = []
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    db_chunk = DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk["chunk_index"],
                        content=chunk["content"],
                        start_char=chunk["start_char"],
                        end_char=chunk["end_char"],
                        page_number=chunk["page_number"],
                        embedding=embedding,
                    )
                    db_chunks.append(db_chunk)

                db.add_all(db_chunks)
                document.status = "completed"
                document.chunk_count = len(chunks)
                await db.commit()

                logger.info(f"Processed document {document_id} into {len(chunks)} chunks")

            except Exception as e:
                logger.error(f"Failed to process document {document_id}: {e}")
                document.status = "failed"
                document.error_message = str(e)
                await db.commit()
                raise

    async def process_document_from_bytes(
        self,
        document_id: int,
        file_bytes: bytes,
        content_type: str,
    ) -> None:
        """Process a document from raw bytes."""
        async with get_db_context() as db:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return

            # Store raw file bytes if enabled and under size limit
            if settings.store_raw_files and len(file_bytes) <= settings.max_file_size_bytes:
                document.file_bytes = file_bytes

            await db.commit()

        # Now process the document
        await self.process_document(document_id)

    async def _parse_document(self, document: Document) -> str:
        """Parse document content from stored bytes or raw_text."""
        # If we have raw_text already, use it (for reprocessing)
        if document.raw_text:
            return document.raw_text

        # Parse from stored file_bytes
        if document.file_bytes:
            return self._parse_bytes(document.file_bytes, document.content_type)

        raise ValueError("No content available to parse")

    def _parse_bytes(self, file_bytes: bytes, content_type: str) -> str:
        """Parse content from bytes based on content type."""
        if content_type == "text/plain" or content_type == "text/markdown":
            return file_bytes.decode("utf-8")
        elif content_type == "application/pdf":
            return self._parse_pdf_bytes(file_bytes)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

    def _parse_pdf_bytes(self, file_bytes: bytes) -> str:
        """Parse PDF from bytes."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []

            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(f"[Page {page_num}]\n{page_text}")

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            raise

    def _chunk_text(self, text: str, source_name: str) -> list[dict]:
        """Split text into overlapping chunks."""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

        if not text:
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Find end position
            end = start + self.chunk_size

            # If not at the end, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                break_point = max(last_period, last_newline)

                if break_point > start + self.chunk_size // 2:
                    end = break_point + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                # Extract page number if present
                page_match = re.search(r'\[Page (\d+)\]', chunk_text)
                page_number = int(page_match.group(1)) if page_match else None

                chunks.append({
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                    "page_number": page_number,
                    "source": source_name,
                })
                chunk_index += 1

            # Move start position with overlap
            start = end - self.chunk_overlap
            if chunks and start <= chunks[-1]["start_char"]:
                start = end  # Prevent infinite loop

        return chunks

    async def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API."""
        if not texts:
            return []

        # Process in batches of 100 (OpenAI limit)
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = await self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=batch,
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def delete_document_chunks(self, document_id: int) -> None:
        """Delete all chunks for a document."""
        async with get_db_context() as db:
            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            await db.commit()

    async def reprocess_document(self, document_id: int) -> None:
        """Reprocess a document using stored raw_text or file_bytes."""
        async with get_db_context() as db:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document {document_id} not found")

            if not document.raw_text and not document.file_bytes:
                raise ValueError("No stored content available for reprocessing")

            document.status = "pending"
            document.error_message = None
            await db.commit()

        await self.process_document(document_id)
