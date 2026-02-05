"""Document ingestion service - parsing, chunking, and embedding."""

import logging
import re
import uuid
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sqlalchemy import select

from src.config import get_settings
from src.database import get_db_context
from src.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()


class IngestionService:
    """Service for ingesting and processing documents."""

    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Initialize embedding function
        self._embedding_function = None

    def _get_embedding_function(self):
        """Lazy load embedding function."""
        if self._embedding_function is None:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            self._embedding_function = OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=settings.embedding_model,
            )
        return self._embedding_function

    async def process_document(self, document_id: int) -> None:
        """Process a document: parse, chunk, embed, and store."""
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

                # Parse document content
                content = await self._parse_document(document)

                # Delete existing chunks if reprocessing
                await self._delete_existing_chunks(db, document_id)

                # Chunk the content
                chunks = self._chunk_text(content, document.original_filename)

                # Create embeddings and store in vector DB
                await self._store_chunks(db, document, chunks)

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

    async def _parse_document(self, document: Document) -> str:
        """Parse document content based on file type."""
        file_path = Path(document.file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content_type = document.content_type

        if content_type == "text/plain" or content_type == "text/markdown":
            return self._parse_text(file_path)
        elif content_type == "application/pdf":
            return self._parse_pdf(file_path)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

    def _parse_text(self, file_path: Path) -> str:
        """Parse plain text file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_pdf(self, file_path: Path) -> str:
        """Parse PDF file."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text_parts = []

            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(f"[Page {page_num}]\n{page_text}")

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            raise

    def _chunk_text(
        self,
        text: str,
        source_name: str,
    ) -> list[dict]:
        """Split text into overlapping chunks."""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

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
            if start <= chunks[-1]["start_char"] if chunks else 0:
                start = end  # Prevent infinite loop

        return chunks

    async def _store_chunks(
        self,
        db,
        document: Document,
        chunks: list[dict],
    ) -> None:
        """Store chunks in database and vector store."""
        if not chunks:
            return

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        db_chunks = []

        for chunk in chunks:
            chroma_id = str(uuid.uuid4())
            ids.append(chroma_id)
            documents.append(chunk["content"])
            metadatas.append({
                "document_id": document.id,
                "document_name": document.original_filename,
                "chunk_index": chunk["chunk_index"],
                "page_number": chunk["page_number"] or -1,
            })

            # Create database record
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                start_char=chunk["start_char"],
                end_char=chunk["end_char"],
                page_number=chunk["page_number"],
                chroma_id=chroma_id,
            )
            db_chunks.append(db_chunk)

        # Store in ChromaDB with embeddings
        embedding_fn = self._get_embedding_function()
        embeddings = embedding_fn(documents)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        # Store in database
        db.add_all(db_chunks)
        await db.commit()

    async def _delete_existing_chunks(self, db, document_id: int) -> None:
        """Delete existing chunks for a document."""
        # Get existing chunk IDs
        result = await db.execute(
            select(DocumentChunk.chroma_id).where(
                DocumentChunk.document_id == document_id
            )
        )
        chroma_ids = [row[0] for row in result.all()]

        # Delete from ChromaDB
        if chroma_ids:
            try:
                self.collection.delete(ids=chroma_ids)
            except Exception as e:
                logger.warning(f"Failed to delete from ChromaDB: {e}")

        # Delete from database
        await db.execute(
            DocumentChunk.__table__.delete().where(
                DocumentChunk.document_id == document_id
            )
        )
        await db.commit()

    async def delete_document_chunks(self, document_id: int) -> None:
        """Delete all chunks for a document."""
        async with get_db_context() as db:
            await self._delete_existing_chunks(db, document_id)
