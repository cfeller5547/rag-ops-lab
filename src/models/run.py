"""Run and Message models for chat sessions."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Run(Base):
    """Represents a chat session/run."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )  # active, completed, failed

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="run", cascade="all, delete-orphan"
    )


class Message(Base):
    """Represents a message in a chat run."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )

    # Message content
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # For assistant messages
    citations: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON array of citations
    is_refusal: Mapped[bool] = mapped_column(default=False)
    refusal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metrics
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="messages")
