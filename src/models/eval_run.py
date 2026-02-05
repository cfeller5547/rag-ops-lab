"""Evaluation run and result models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class EvalRun(Base):
    """Represents an evaluation run."""

    __tablename__ = "eval_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    eval_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dataset info
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, running, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Aggregate metrics
    groundedness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hallucination_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    schema_compliance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tool_correctness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_p95_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    results: Mapped[list["EvalResult"]] = relationship(
        "EvalResult", back_populates="eval_run", cascade="all, delete-orphan"
    )


class EvalResult(Base):
    """Represents a single evaluation case result."""

    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    eval_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("eval_runs.id", ondelete="CASCADE"), nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Input/Output
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actual_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Per-case metrics
    groundedness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hallucination_detected: Mapped[Optional[bool]] = mapped_column(nullable=True)
    schema_compliant: Mapped[Optional[bool]] = mapped_column(nullable=True)
    tool_calls_correct: Mapped[Optional[bool]] = mapped_column(nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, passed, failed, error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    eval_run: Mapped["EvalRun"] = relationship("EvalRun", back_populates="results")
