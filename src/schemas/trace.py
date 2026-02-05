"""Trace-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class TraceEventResponse(BaseModel):
    """Schema for a trace event response."""

    id: int
    trace_id: str
    run_id: str
    session_id: str
    event_type: Literal["retrieval", "tool_call", "model_call", "validation", "error"]
    event_name: str
    event_data: dict[str, Any] = Field(..., description="Event details as JSON")
    duration_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class TraceListResponse(BaseModel):
    """Schema for trace list response (grouped by run)."""

    traces: list[dict] = Field(
        ...,
        description="List of traces grouped by run_id with summary info",
    )
    total: int
    page: int = 1
    page_size: int = 20


class TraceSummary(BaseModel):
    """Summary of a trace/run for listing."""

    run_id: str
    session_id: str
    event_count: int
    total_duration_ms: int
    total_tokens: int
    total_cost_usd: float
    status: str  # success, error, partial
    first_event_at: datetime
    last_event_at: datetime


class TraceDetailResponse(BaseModel):
    """Schema for detailed trace response with all events."""

    run_id: str
    session_id: str
    events: list[TraceEventResponse]
    summary: dict[str, Any] = Field(
        ...,
        description="Summary statistics for the trace",
    )


class TraceReplayRequest(BaseModel):
    """Schema for replaying a trace."""

    run_id: str = Field(..., description="Run ID to replay")
    include_timing: bool = Field(
        True, description="Whether to simulate original timing"
    )
