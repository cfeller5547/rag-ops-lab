"""Chat-related Pydantic schemas."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Schema for a citation reference."""

    document_id: int = Field(..., description="ID of the source document")
    document_name: str = Field(..., description="Name of the source document")
    chunk_id: int = Field(..., description="ID of the chunk")
    chunk_index: int = Field(..., description="Index of the chunk in the document")
    content: str = Field(..., description="The cited content")
    page_number: Optional[int] = Field(None, description="Page number if available")
    relevance_score: float = Field(..., description="Relevance score from retrieval")


class ChatMessage(BaseModel):
    """Schema for a chat message."""

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Role of the message sender"
    )
    content: str = Field(..., description="Message content")
    citations: Optional[list[Citation]] = Field(
        None, description="Citations for assistant messages"
    )
    is_refusal: bool = Field(False, description="Whether this is a refusal response")
    refusal_reason: Optional[str] = Field(
        None, description="Reason for refusal if applicable"
    )
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Schema for chat request."""

    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation continuity"
    )
    include_sources: bool = Field(
        True, description="Whether to include source citations"
    )
    max_sources: int = Field(5, description="Maximum number of sources to retrieve")


class ChatResponse(BaseModel):
    """Schema for chat response."""

    run_id: str = Field(..., description="Unique run identifier")
    session_id: str = Field(..., description="Session identifier")
    message: ChatMessage = Field(..., description="Assistant response message")
    latency_ms: int = Field(..., description="Response latency in milliseconds")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")


class StreamChunk(BaseModel):
    """Schema for streaming response chunk."""

    type: Literal["content", "citation", "done", "error"] = Field(
        ..., description="Type of chunk"
    )
    content: Optional[str] = Field(None, description="Content for content chunks")
    citation: Optional[Citation] = Field(None, description="Citation for citation chunks")
    error: Optional[str] = Field(None, description="Error message for error chunks")
    run_id: Optional[str] = Field(None, description="Run ID (sent with done chunk)")
    session_id: Optional[str] = Field(
        None, description="Session ID (sent with done chunk)"
    )
