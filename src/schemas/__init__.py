"""Pydantic schemas for RAGOps Lab API."""

from src.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Citation,
    StreamChunk,
)
from src.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentChunkResponse,
    DocumentListResponse,
)
from src.schemas.eval import (
    EvalCase,
    EvalDataset,
    EvalMetrics,
    EvalResultResponse,
    EvalRunRequest,
    EvalRunResponse,
    EvalRunListResponse,
)
from src.schemas.trace import (
    TraceEventResponse,
    TraceListResponse,
    TraceDetailResponse,
)

__all__ = [
    # Chat
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "Citation",
    "StreamChunk",
    # Document
    "DocumentCreate",
    "DocumentResponse",
    "DocumentChunkResponse",
    "DocumentListResponse",
    # Eval
    "EvalCase",
    "EvalDataset",
    "EvalMetrics",
    "EvalResultResponse",
    "EvalRunRequest",
    "EvalRunResponse",
    "EvalRunListResponse",
    # Trace
    "TraceEventResponse",
    "TraceListResponse",
    "TraceDetailResponse",
]
