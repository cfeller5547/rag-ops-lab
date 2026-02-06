"""Retrieval service with pgvector similarity search and reranking."""

import logging
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

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


class RetrievalService:
    """Service for retrieving relevant document chunks using pgvector."""

    def __init__(self):
        self.top_k = settings.top_k_retrieval
        self.rerank_top_k = settings.rerank_top_k
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._reranker = None

    def _get_reranker(self):
        """Lazy load the reranker model."""
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder(settings.rerank_model)
                logger.info(f"Loaded reranker model: {settings.rerank_model}")
            except Exception as e:
                logger.warning(f"Failed to load reranker: {e}. Reranking disabled.")
                self._reranker = False  # Mark as unavailable
        return self._reranker if self._reranker else None

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_ids: Optional[list[int]] = None,
        rerank: bool = True,
    ) -> list[RetrievalResult]:
        """Search for relevant document chunks using pgvector."""
        k = top_k or self.top_k

        # Generate query embedding
        query_embedding = await self._generate_embedding(query)

        async with get_db_context() as db:
            # Build pgvector similarity search query
            # Using cosine distance: 1 - (embedding <=> query_embedding)
            results = await self._vector_search(
                db, query_embedding, k, document_ids
            )

        if not results:
            return []

        # Rerank if enabled and reranker is available
        if rerank and len(results) > 1:
            reranker = self._get_reranker()
            if reranker:
                results = self._rerank_results(query, results)

        # Return top results after reranking
        return results[:self.rerank_top_k if rerank else k]

    async def _vector_search(
        self,
        db: AsyncSession,
        query_embedding: list[float],
        top_k: int,
        document_ids: Optional[list[int]] = None,
    ) -> list[RetrievalResult]:
        """Perform pgvector similarity search."""
        # Build the query with cosine similarity
        # pgvector uses <=> for cosine distance, so similarity = 1 - distance
        # Note: We embed the vector directly in SQL since asyncpg has issues with ::vector cast
        embedding_str = f"'[{','.join(str(x) for x in query_embedding)}]'::vector"

        base_query = f"""
            SELECT
                dc.id as chunk_id,
                dc.document_id,
                d.original_filename as document_name,
                dc.content,
                dc.chunk_index,
                dc.page_number,
                1 - (dc.embedding <=> {embedding_str}) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.embedding IS NOT NULL
        """

        if document_ids:
            doc_ids_str = ",".join(str(d) for d in document_ids)
            base_query += f" AND dc.document_id IN ({doc_ids_str})"

        base_query += f"""
            ORDER BY dc.embedding <=> {embedding_str}
            LIMIT {top_k}
        """

        result = await db.execute(text(base_query))
        rows = result.fetchall()

        return [
            RetrievalResult(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                document_name=row.document_name,
                content=row.content,
                chunk_index=row.chunk_index,
                page_number=row.page_number,
                relevance_score=float(row.similarity) if row.similarity else 0.0,
            )
            for row in rows
        ]

    def _rerank_results(
        self,
        query: str,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Rerank results using cross-encoder."""
        reranker = self._get_reranker()
        if not reranker:
            return results

        # Prepare pairs for reranking
        pairs = [(query, r.content) for r in results]

        # Get reranking scores
        scores = reranker.predict(pairs)

        # Update scores and sort
        for i, result in enumerate(results):
            # Combine original score with rerank score (weighted)
            original_weight = 0.3
            rerank_weight = 0.7
            combined_score = (
                original_weight * result.relevance_score +
                rerank_weight * float(scores[i])
            )
            result.relevance_score = combined_score

        # Sort by combined score
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        return results

    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        response = await self.openai_client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding

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

    async def get_stats(self) -> dict:
        """Get statistics about the vector store."""
        async with get_db_context() as db:
            # Count total chunks
            result = await db.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
            )
            chunk_count = result.scalar() or 0

            # Count documents
            result = await db.execute(
                text("SELECT COUNT(*) FROM documents WHERE status = 'completed'")
            )
            doc_count = result.scalar() or 0

            return {
                "total_chunks": chunk_count,
                "total_documents": doc_count,
                "embedding_dimensions": settings.embedding_dimensions,
                "reranking_enabled": self._get_reranker() is not None,
            }
