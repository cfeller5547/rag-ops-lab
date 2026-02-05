"""Trace API endpoints."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.trace import TraceEvent
from src.schemas.trace import (
    TraceDetailResponse,
    TraceEventResponse,
    TraceListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=TraceListResponse)
async def list_traces(
    page: int = 1,
    page_size: int = 20,
    session_id: Optional[str] = None,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> TraceListResponse:
    """List traces grouped by run_id with pagination."""
    offset = (page - 1) * page_size

    # Subquery to get unique run_ids with aggregated stats
    base_query = select(
        TraceEvent.run_id,
        TraceEvent.session_id,
        func.count(TraceEvent.id).label("event_count"),
        func.sum(TraceEvent.duration_ms).label("total_duration_ms"),
        func.sum(TraceEvent.tokens_in + TraceEvent.tokens_out).label("total_tokens"),
        func.sum(TraceEvent.cost_usd).label("total_cost_usd"),
        func.min(TraceEvent.timestamp).label("first_event_at"),
        func.max(TraceEvent.timestamp).label("last_event_at"),
    ).group_by(TraceEvent.run_id, TraceEvent.session_id)

    if session_id:
        base_query = base_query.where(TraceEvent.session_id == session_id)
    if event_type:
        base_query = base_query.where(TraceEvent.event_type == event_type)

    # Get total count of unique runs
    count_subquery = base_query.subquery()
    count_result = await db.execute(select(func.count()).select_from(count_subquery))
    total = count_result.scalar() or 0

    # Get paginated results
    query = base_query.order_by(func.max(TraceEvent.timestamp).desc())
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    traces = []
    for row in rows:
        # Check if any event has error status
        error_check = await db.execute(
            select(TraceEvent.status)
            .where(TraceEvent.run_id == row.run_id)
            .where(TraceEvent.status == "error")
            .limit(1)
        )
        has_error = error_check.scalar_one_or_none() is not None

        traces.append({
            "run_id": row.run_id,
            "session_id": row.session_id,
            "event_count": row.event_count,
            "total_duration_ms": row.total_duration_ms or 0,
            "total_tokens": row.total_tokens or 0,
            "total_cost_usd": float(row.total_cost_usd or 0),
            "status": "error" if has_error else "success",
            "first_event_at": row.first_event_at.isoformat() if row.first_event_at else None,
            "last_event_at": row.last_event_at.isoformat() if row.last_event_at else None,
        })

    return TraceListResponse(
        traces=traces,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{run_id}", response_model=TraceDetailResponse)
async def get_trace(
    run_id: str,
    db: AsyncSession = Depends(get_db),
) -> TraceDetailResponse:
    """Get detailed trace for a run."""
    result = await db.execute(
        select(TraceEvent)
        .where(TraceEvent.run_id == run_id)
        .order_by(TraceEvent.timestamp)
    )
    events = result.scalars().all()

    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace for run '{run_id}' not found",
        )

    # Build response
    event_responses = []
    total_duration = 0
    total_tokens = 0
    total_cost = 0.0
    event_type_counts = {}

    for event in events:
        event_data = json.loads(event.event_data) if event.event_data else {}
        event_responses.append(
            TraceEventResponse(
                id=event.id,
                trace_id=event.trace_id,
                run_id=event.run_id,
                session_id=event.session_id,
                event_type=event.event_type,
                event_name=event.event_name,
                event_data=event_data,
                duration_ms=event.duration_ms,
                tokens_in=event.tokens_in,
                tokens_out=event.tokens_out,
                cost_usd=event.cost_usd,
                status=event.status,
                error_message=event.error_message,
                timestamp=event.timestamp,
            )
        )

        if event.duration_ms:
            total_duration += event.duration_ms
        if event.tokens_in:
            total_tokens += event.tokens_in
        if event.tokens_out:
            total_tokens += event.tokens_out
        if event.cost_usd:
            total_cost += event.cost_usd

        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1

    summary = {
        "total_events": len(events),
        "total_duration_ms": total_duration,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "event_type_counts": event_type_counts,
        "has_errors": any(e.status == "error" for e in events),
    }

    return TraceDetailResponse(
        run_id=run_id,
        session_id=events[0].session_id if events else "",
        events=event_responses,
        summary=summary,
    )


@router.get("/{run_id}/events")
async def get_trace_events(
    run_id: str,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[TraceEventResponse]:
    """Get all events for a trace, optionally filtered by type."""
    query = select(TraceEvent).where(TraceEvent.run_id == run_id)

    if event_type:
        query = query.where(TraceEvent.event_type == event_type)

    query = query.order_by(TraceEvent.timestamp)
    result = await db.execute(query)
    events = result.scalars().all()

    return [
        TraceEventResponse(
            id=event.id,
            trace_id=event.trace_id,
            run_id=event.run_id,
            session_id=event.session_id,
            event_type=event.event_type,
            event_name=event.event_name,
            event_data=json.loads(event.event_data) if event.event_data else {},
            duration_ms=event.duration_ms,
            tokens_in=event.tokens_in,
            tokens_out=event.tokens_out,
            cost_usd=event.cost_usd,
            status=event.status,
            error_message=event.error_message,
            timestamp=event.timestamp,
        )
        for event in events
    ]


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trace(
    run_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete all trace events for a run."""
    result = await db.execute(
        select(TraceEvent).where(TraceEvent.run_id == run_id).limit(1)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace for run '{run_id}' not found",
        )

    await db.execute(
        TraceEvent.__table__.delete().where(TraceEvent.run_id == run_id)
    )
    await db.commit()
