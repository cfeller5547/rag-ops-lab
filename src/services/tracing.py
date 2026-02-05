"""Tracing service for observability."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.trace import TraceEvent

logger = logging.getLogger(__name__)


# Approximate costs per 1K tokens (as of 2024)
MODEL_COSTS = {
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "text-embedding-3-small": {"input": 0.00002, "output": 0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0},
}


def _estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate cost based on model and token counts."""
    costs = MODEL_COSTS.get(model, {"input": 0.01, "output": 0.03})
    return (tokens_in / 1000 * costs["input"]) + (tokens_out / 1000 * costs["output"])


class TracingService:
    """Service for capturing and storing trace events."""

    def __init__(self, run_id: str, session_id: str):
        self.run_id = run_id
        self.session_id = session_id
        self.trace_id = str(uuid.uuid4())
        self.events: list[TraceEvent] = []

    async def log_retrieval(
        self,
        query: str,
        results: list[dict],
        duration_ms: int,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> None:
        """Log a retrieval event."""
        event = TraceEvent(
            trace_id=self.trace_id,
            run_id=self.run_id,
            session_id=self.session_id,
            event_type="retrieval",
            event_name="vector_search",
            event_data=json.dumps({
                "query": query,
                "results_count": len(results),
                "results": results,
            }),
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            timestamp=datetime.utcnow(),
        )
        self.events.append(event)

    async def log_model_call(
        self,
        model: str,
        messages: list[dict],
        response: str,
        tokens_in: int,
        tokens_out: int,
        duration_ms: int,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> None:
        """Log a model/LLM call event."""
        cost = _estimate_cost(model, tokens_in, tokens_out)

        event = TraceEvent(
            trace_id=self.trace_id,
            run_id=self.run_id,
            session_id=self.session_id,
            event_type="model_call",
            event_name=model,
            event_data=json.dumps({
                "model": model,
                "messages_count": len(messages),
                "response_preview": response[:500] if response else "",
            }),
            duration_ms=duration_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            status=status,
            error_message=error_message,
            timestamp=datetime.utcnow(),
        )
        self.events.append(event)

    async def log_tool_call(
        self,
        tool_name: str,
        tool_args: dict,
        tool_output: Any,
        duration_ms: int,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> None:
        """Log a tool call event."""
        event = TraceEvent(
            trace_id=self.trace_id,
            run_id=self.run_id,
            session_id=self.session_id,
            event_type="tool_call",
            event_name=tool_name,
            event_data=json.dumps({
                "tool_name": tool_name,
                "args": tool_args,
                "output_preview": str(tool_output)[:500] if tool_output else "",
            }),
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            timestamp=datetime.utcnow(),
        )
        self.events.append(event)

    async def log_validation(
        self,
        validation_type: str,
        input_data: Any,
        is_valid: bool,
        errors: Optional[list[str]] = None,
        duration_ms: int = 0,
    ) -> None:
        """Log a validation event."""
        event = TraceEvent(
            trace_id=self.trace_id,
            run_id=self.run_id,
            session_id=self.session_id,
            event_type="validation",
            event_name=validation_type,
            event_data=json.dumps({
                "validation_type": validation_type,
                "is_valid": is_valid,
                "errors": errors or [],
            }),
            duration_ms=duration_ms,
            status="success" if is_valid else "retry",
            timestamp=datetime.utcnow(),
        )
        self.events.append(event)

    async def log_error(
        self,
        error_message: str,
        error_type: str = "general",
        context: Optional[dict] = None,
    ) -> None:
        """Log an error event."""
        event = TraceEvent(
            trace_id=self.trace_id,
            run_id=self.run_id,
            session_id=self.session_id,
            event_type="error",
            event_name=error_type,
            event_data=json.dumps({
                "error_type": error_type,
                "context": context or {},
            }),
            status="error",
            error_message=error_message,
            timestamp=datetime.utcnow(),
        )
        self.events.append(event)

    async def flush(self, db: AsyncSession) -> None:
        """Flush all events to the database."""
        if not self.events:
            return

        try:
            db.add_all(self.events)
            await db.commit()
            self.events = []
        except Exception as e:
            logger.error(f"Failed to flush trace events: {e}")
            await db.rollback()
            raise

    def get_summary(self) -> dict:
        """Get a summary of the current trace."""
        total_duration = sum(e.duration_ms or 0 for e in self.events)
        total_tokens = sum((e.tokens_in or 0) + (e.tokens_out or 0) for e in self.events)
        total_cost = sum(e.cost_usd or 0 for e in self.events)

        event_counts = {}
        for event in self.events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "event_count": len(self.events),
            "event_counts": event_counts,
            "total_duration_ms": total_duration,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "has_errors": any(e.status == "error" for e in self.events),
        }
