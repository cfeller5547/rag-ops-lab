"""Trace event model for observability."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class TraceEvent(Base):
    """Represents a trace event in the observability system."""

    __tablename__ = "trace_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Event type
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # retrieval, tool_call, model_call, validation, error

    # Event details (JSON)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON

    # Metrics
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="success"
    )  # success, error, retry
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
