"""Retrieval service for vector search."""

import logging
from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sqlalchemy import select

from src.config import get_settings
from src.database import get_db_context
from src.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RetrievalResult:
    """Result from vector search."""

    chunk_id: int
    document_id: int
    document_name: str
    content: str
    chunk_index: int
    page_number: Optional[int]
    relevance_score: float
    chroma_id: str


class RetrievalService:
    """Service for retrieving relevant document chunks."""

    def __init__(self):
        self.top_k = settings.top_k_retrieval

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

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_ids: Optional[list[int]] = None,
        min_score: float = 0.0,
    ) -> list[RetrievalResult]:
        """Search for relevant document chunks."""
        k = top_k or self.top_k

        # Build where filter
        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}

        # Get query embedding
        embedding_fn = self._get_embedding_function()
        query_embedding = embedding_fn([query])[0]

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        # Convert to RetrievalResult objects
        retrieval_results = []

        for i, chroma_id in enumerate(results["ids"][0]):
            # ChromaDB returns distances (lower is better), convert to similarity score
            distance = results["distances"][0][i] if results["distances"] else 0
            # Cosine distance to similarity: similarity = 1 - distance
            score = 1 - distance

            if score < min_score:
                continue

            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            content = results["documents"][0][i] if results["documents"] else ""

            # Get chunk ID from database
            chunk_id = await self._get_chunk_id(chroma_id)

            retrieval_results.append(
                RetrievalResult(
                    chunk_id=chunk_id or 0,
                    document_id=metadata.get("document_id", 0),
                    document_name=metadata.get("document_name", "Unknown"),
                    content=content,
                    chunk_index=metadata.get("chunk_index", 0),
                    page_number=metadata.get("page_number") if metadata.get("page_number", -1) != -1 else None,
                    relevance_score=score,
                    chroma_id=chroma_id,
                )
            )

        return retrieval_results

    async def _get_chunk_id(self, chroma_id: str) -> Optional[int]:
        """Get database chunk ID from ChromaDB ID."""
        async with get_db_context() as db:
            result = await db.execute(
                select(DocumentChunk.id).where(DocumentChunk.chroma_id == chroma_id)
            )
            row = result.scalar_one_or_none()
            return row

    async def get_chunk_by_id(self, chunk_id: int) -> Optional[dict]:
        """Get a specific chunk by its database ID."""
        async with get_db_context() as db:
            result = await db.execute(
                select(DocumentChunk, Document)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.id == chunk_id)
            )
            row = result.one_or_none()

            if not row:
                return None

            chunk, document = row
            return {
                "chunk_id": chunk.id,
                "document_id": document.id,
                "document_name": document.original_filename,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
            }

    async def get_document_chunks(self, document_id: int) -> list[dict]:
        """Get all chunks for a document."""
        async with get_db_context() as db:
            result = await db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()

            return [
                {
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                }
                for chunk in chunks
            ]

    def get_collection_stats(self) -> dict:
        """Get statistics about the vector collection."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": settings.chroma_collection_name,
        }
