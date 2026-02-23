"""RAG Agent service with tool calling and structured JSON outputs."""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Literal, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.config import get_settings
from src.schemas.chat import Citation, StreamChunk
from src.services.retrieval import RetrievalService, RetrievalResult
from src.services.tracing import TracingService

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Tool definitions (OpenAI function calling format)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_corpus",
            "description": (
                "Search the document corpus for relevant information. "
                "Call this before answering any factual question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant document chunks",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (1-10)",
                        "default": 5,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_date",
            "description": (
                "Get the current date. Use when the question involves "
                "time-sensitive or date-specific information."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class StructuredAnswer(BaseModel):
    """Structured response produced by the LLM via OpenAI structured outputs."""

    answer: str
    cited_sources: list[int]  # 1-based source indices actually used, e.g. [1, 2]
    is_refusal: bool
    confidence: Literal["high", "medium", "low"]


# ---------------------------------------------------------------------------
# Agent response + helpers
# ---------------------------------------------------------------------------

@dataclass
class AgentResponse:
    """Response from the RAG agent."""

    content: str
    citations: list[Citation] = field(default_factory=list)
    is_refusal: bool = False
    refusal_reason: Optional[str] = None
    tokens_used: Optional[int] = None
    confidence: Optional[str] = None          # "high" | "medium" | "low"
    tools_called: list[str] = field(default_factory=list)  # tool names invoked


SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on searched document context.

IMPORTANT RULES:
1. Use the search_corpus tool to retrieve information before answering any factual question.
2. ONLY answer using information returned by the search tool.
3. ALWAYS cite your sources using [n] notation where n is the source number from search results.
4. If the search returns no relevant results, set is_refusal=true in your response.
5. Never make up or infer information not present in the search results.
6. Use get_date if the question involves current date or time-sensitive context.

When citing sources:
- Use inline citations like "According to the employee handbook [1], ..."
- Each distinct piece of information should have a citation
- Multiple sources can be cited together like [1][2]

Set confidence based on how well the search results support your answer:
- high: results directly and clearly answer the question
- medium: results partially address the question
- low: results are tangentially related or sparse"""


def _format_context(results: list[RetrievalResult]) -> str:
    """Format retrieval results into context string for the LLM."""
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
    """Convert retrieval results to Citation schema objects."""
    return [
        Citation(
            document_id=r.document_id,
            document_name=r.document_name,
            chunk_id=r.chunk_id,
            chunk_index=r.chunk_index,
            content=r.content[:500],
            page_number=r.page_number,
            relevance_score=r.relevance_score,
        )
        for r in results
    ]


# ---------------------------------------------------------------------------
# RAGAgent
# ---------------------------------------------------------------------------

class RAGAgent:
    """Agentic RAG system using OpenAI tool calling and structured outputs."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.retrieval_service = RetrievalService()

    async def _execute_tool_loop(
        self,
        message: str,
        max_sources: int,
        tracer: Optional[TracingService],
    ) -> tuple[list[dict], list[RetrievalResult], list[str]]:
        """
        First OpenAI call with tools enabled.  Execute any requested tool calls
        (search_corpus, get_date) and return the updated messages list, all
        retrieval results accumulated, and the names of tools that were called.
        """
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]

        # First call: let the LLM decide which tools to invoke
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
        )

        all_results: list[RetrievalResult] = []
        tools_called: list[str] = []

        if response.choices[0].finish_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls or []
            # Append the assistant message with tool_calls so the next call has context
            messages.append(response.choices[0].message)

            for tc in tool_calls:
                tools_called.append(tc.function.name)

                if tc.function.name == "search_corpus":
                    args = json.loads(tc.function.arguments)
                    retrieval_start = time.time()
                    results = await self.retrieval_service.search(
                        query=args["query"],
                        top_k=args.get("top_k", max_sources),
                    )
                    retrieval_duration = int((time.time() - retrieval_start) * 1000)
                    all_results.extend(results)

                    if tracer:
                        await tracer.log_retrieval(
                            query=args["query"],
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

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": _format_context(results) if results else "No relevant documents found.",
                    })

                elif tc.function.name == "get_date":
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": datetime.now().strftime("%Y-%m-%d"),
                    })

        return messages, all_results, tools_called

    async def chat(
        self,
        message: str,
        session_id: str,
        max_sources: int = 5,
        tracer: Optional[TracingService] = None,
    ) -> AgentResponse:
        """Process a chat message using tool calling + structured outputs."""
        start_time = time.time()

        # Step 1: Tool calling loop (LLM decides when/how to search)
        messages, results, tools_called = await self._execute_tool_loop(
            message, max_sources, tracer
        )

        # Step 2: Refusal check — no relevant context found
        if not results or all(r.relevance_score < 0.3 for r in results):
            return AgentResponse(
                content=(
                    "I cannot answer this question based on the available documents. "
                    "The uploaded documents don't appear to contain information relevant "
                    "to your question. Please try uploading relevant documents or asking "
                    "about topics covered in the existing corpus."
                ),
                citations=[],
                is_refusal=True,
                refusal_reason="No relevant documents found",
                tools_called=tools_called,
            )

        all_citations = _results_to_citations(results)

        # Step 3: Structured output call — LLM formats final answer as JSON
        model_start = time.time()
        try:
            completion = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=StructuredAnswer,
                temperature=0.3,
                max_tokens=1500,
            )
            model_duration = int((time.time() - model_start) * 1000)
            structured = completion.choices[0].message.parsed

            if tracer:
                await tracer.log_model_call(
                    model=self.model,
                    messages=messages,
                    response=structured.answer if structured else "",
                    tokens_in=completion.usage.prompt_tokens if completion.usage else 0,
                    tokens_out=completion.usage.completion_tokens if completion.usage else 0,
                    duration_ms=model_duration,
                )

            if structured is None:
                raise ValueError("Structured output parsing returned None")

            # Map cited_sources (1-based indices) to actual citation objects
            cited = [
                all_citations[i - 1]
                for i in structured.cited_sources
                if 0 < i <= len(all_citations)
            ]

            return AgentResponse(
                content=structured.answer,
                citations=cited if not structured.is_refusal else [],
                is_refusal=structured.is_refusal,
                refusal_reason="Insufficient context" if structured.is_refusal else None,
                tokens_used=completion.usage.total_tokens if completion.usage else None,
                confidence=structured.confidence,
                tools_called=tools_called,
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
        """Stream a chat response. Tool loop runs first, then streams final answer."""
        # Step 1: Tool calling loop (synchronous — tools must complete before streaming)
        messages, results, tools_called = await self._execute_tool_loop(
            message, max_sources, tracer
        )

        # Send citations up front so the UI can render them immediately
        citations = _results_to_citations(results)
        for citation in citations:
            yield StreamChunk(type="citation", citation=citation)

        # Step 2: Refusal check
        if not results or all(r.relevance_score < 0.3 for r in results):
            yield StreamChunk(
                type="content",
                content=(
                    "I cannot answer this question based on the available documents. "
                    "The uploaded documents don't appear to contain information relevant to your question."
                ),
            )
            return

        # Step 3: Stream final response
        # (Structured outputs are not used here — they require accumulating the full
        # response before parsing, which defeats the purpose of streaming.)
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
                    tokens_in=0,  # Not available in streaming mode
                    tokens_out=0,
                    duration_ms=model_duration,
                )

        except Exception as e:
            logger.error(f"Stream error: {e}")
            if tracer:
                await tracer.log_error(f"Stream error: {e}")
            yield StreamChunk(type="error", error=str(e))
