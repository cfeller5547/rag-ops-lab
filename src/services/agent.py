"""RAG Agent service with tool calling and citation support."""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from src.config import get_settings
from src.schemas.chat import Citation, StreamChunk
from src.services.retrieval import RetrievalService, RetrievalResult
from src.services.tracing import TracingService

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AgentResponse:
    """Response from the RAG agent."""

    content: str
    citations: list[Citation] = field(default_factory=list)
    is_refusal: bool = False
    refusal_reason: Optional[str] = None
    tokens_used: Optional[int] = None


SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.

IMPORTANT RULES:
1. ONLY answer questions using information from the provided context.
2. ALWAYS cite your sources using [n] notation where n is the source number.
3. If the context doesn't contain enough information to answer the question, say so clearly.
4. Never make up or infer information not present in the context.
5. If asked about topics not covered in the context, politely decline and explain what topics are available.

When citing sources:
- Use inline citations like "According to the employee handbook [1], ..."
- Each distinct piece of information should have a citation
- Multiple sources can be cited together like [1][2]

If you cannot answer the question from the provided context:
- Start with "I cannot answer this question based on the available documents."
- Explain what information would be needed
- Suggest related topics that ARE covered in the context if applicable"""


def _format_context(results: list[RetrievalResult]) -> str:
    """Format retrieval results into context for the LLM."""
    if not results:
        return "No relevant documents found."

    context_parts = []
    for i, result in enumerate(results, 1):
        page_info = f" (Page {result.page_number})" if result.page_number else ""
        context_parts.append(
            f"[Source {i}] From '{result.document_name}'{page_info}:\n{result.content}"
        )

    return "\n\n---\n\n".join(context_parts)


def _results_to_citations(results: list[RetrievalResult]) -> list[Citation]:
    """Convert retrieval results to citations."""
    return [
        Citation(
            document_id=r.document_id,
            document_name=r.document_name,
            chunk_id=r.chunk_id,
            chunk_index=r.chunk_index,
            content=r.content[:500],  # Truncate for response
            page_number=r.page_number,
            relevance_score=r.relevance_score,
        )
        for r in results
    ]


class RAGAgent:
    """Agentic RAG system with citations and refusal capability."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.retrieval_service = RetrievalService()

    async def chat(
        self,
        message: str,
        session_id: str,
        max_sources: int = 5,
        tracer: Optional[TracingService] = None,
    ) -> AgentResponse:
        """Process a chat message and return a response with citations."""
        start_time = time.time()

        # Step 1: Retrieve relevant documents
        retrieval_start = time.time()
        results = await self.retrieval_service.search(
            query=message,
            top_k=max_sources,
        )
        retrieval_duration = int((time.time() - retrieval_start) * 1000)

        if tracer:
            await tracer.log_retrieval(
                query=message,
                results=[
                    {
                        "document_id": r.document_id,
                        "document_name": r.document_name,
                        "chunk_index": r.chunk_index,
                        "score": r.relevance_score,
                    }
                    for r in results
                ],
                duration_ms=retrieval_duration,
            )

        # Step 2: Check if we have relevant context
        if not results or all(r.relevance_score < 0.3 for r in results):
            return AgentResponse(
                content="I cannot answer this question based on the available documents. The uploaded documents don't appear to contain information relevant to your question. Please try uploading relevant documents or asking about topics covered in the existing corpus.",
                citations=[],
                is_refusal=True,
                refusal_reason="No relevant documents found",
            )

        # Step 3: Format context and generate response
        context = _format_context(results)
        citations = _results_to_citations(results)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\n---\n\nQuestion: {message}",
            },
        ]

        # Step 4: Call LLM
        model_start = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
            )
            model_duration = int((time.time() - model_start) * 1000)

            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else None

            if tracer:
                await tracer.log_model_call(
                    model=self.model,
                    messages=messages,
                    response=content,
                    tokens_in=response.usage.prompt_tokens if response.usage else 0,
                    tokens_out=response.usage.completion_tokens if response.usage else 0,
                    duration_ms=model_duration,
                )

            # Check if response is a refusal
            is_refusal = content.lower().startswith("i cannot answer")

            return AgentResponse(
                content=content,
                citations=citations if not is_refusal else [],
                is_refusal=is_refusal,
                refusal_reason="Insufficient context" if is_refusal else None,
                tokens_used=tokens_used,
            )

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            if tracer:
                await tracer.log_error(f"LLM call failed: {e}")
            raise

    async def chat_stream(
        self,
        message: str,
        session_id: str,
        max_sources: int = 5,
        tracer: Optional[TracingService] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a chat response with citations."""
        # Step 1: Retrieve relevant documents
        retrieval_start = time.time()
        results = await self.retrieval_service.search(
            query=message,
            top_k=max_sources,
        )
        retrieval_duration = int((time.time() - retrieval_start) * 1000)

        if tracer:
            await tracer.log_retrieval(
                query=message,
                results=[
                    {
                        "document_id": r.document_id,
                        "document_name": r.document_name,
                        "chunk_index": r.chunk_index,
                        "score": r.relevance_score,
                    }
                    for r in results
                ],
                duration_ms=retrieval_duration,
            )

        # Send citations first
        citations = _results_to_citations(results)
        for citation in citations:
            yield StreamChunk(type="citation", citation=citation)

        # Check if we have relevant context
        if not results or all(r.relevance_score < 0.3 for r in results):
            yield StreamChunk(
                type="content",
                content="I cannot answer this question based on the available documents. The uploaded documents don't appear to contain information relevant to your question.",
            )
            return

        # Format context and generate response
        context = _format_context(results)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\n---\n\nQuestion: {message}",
            },
        ]

        # Stream LLM response
        model_start = time.time()
        full_content = ""

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield StreamChunk(type="content", content=content)

            model_duration = int((time.time() - model_start) * 1000)

            if tracer:
                await tracer.log_model_call(
                    model=self.model,
                    messages=messages,
                    response=full_content,
                    tokens_in=0,  # Not available in streaming
                    tokens_out=0,
                    duration_ms=model_duration,
                )

        except Exception as e:
            logger.error(f"Stream error: {e}")
            if tracer:
                await tracer.log_error(f"Stream error: {e}")
            yield StreamChunk(type="error", error=str(e))
