"""Chat API endpoints."""

import json
import logging
import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.chat import ChatRequest, ChatResponse, ChatMessage, StreamChunk
from src.services.agent import RAGAgent
from src.services.tracing import TracingService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Send a chat message and get a response with citations."""
    start_time = time.time()
    run_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())

    # Initialize services
    agent = RAGAgent()
    tracer = TracingService(run_id=run_id, session_id=session_id)

    try:
        # Get response from agent
        response = await agent.chat(
            message=request.message,
            session_id=session_id,
            max_sources=request.max_sources,
            tracer=tracer,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Build response message
        message = ChatMessage(
            role="assistant",
            content=response.content,
            citations=response.citations if request.include_sources else None,
            is_refusal=response.is_refusal,
            refusal_reason=response.refusal_reason,
        )

        # Save trace events
        await tracer.flush(db)

        return ChatResponse(
            run_id=run_id,
            session_id=session_id,
            message=message,
            latency_ms=latency_ms,
            tokens_used=response.tokens_used,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        await tracer.log_error(str(e))
        await tracer.flush(db)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream a chat response with citations."""
    run_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())

    async def generate() -> AsyncGenerator[str, None]:
        agent = RAGAgent()
        tracer = TracingService(run_id=run_id, session_id=session_id)

        try:
            async for chunk in agent.chat_stream(
                message=request.message,
                session_id=session_id,
                max_sources=request.max_sources,
                tracer=tracer,
            ):
                yield f"data: {chunk.model_dump_json()}\n\n"

            # Send done chunk
            done_chunk = StreamChunk(
                type="done",
                run_id=run_id,
                session_id=session_id,
            )
            yield f"data: {done_chunk.model_dump_json()}\n\n"

            # Save trace events
            await tracer.flush(db)

        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_chunk = StreamChunk(type="error", error=str(e))
            yield f"data: {error_chunk.model_dump_json()}\n\n"
            await tracer.log_error(str(e))
            await tracer.flush(db)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get chat history for a session."""
    from sqlalchemy import select
    from src.models.run import Run, Message

    # Get runs for this session
    result = await db.execute(
        select(Run)
        .where(Run.session_id == session_id)
        .order_by(Run.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()

    history = []
    for run in runs:
        messages_result = await db.execute(
            select(Message)
            .where(Message.run_id == run.id)
            .order_by(Message.created_at)
        )
        messages = messages_result.scalars().all()

        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
                "citations": json.loads(msg.citations) if msg.citations else None,
                "is_refusal": msg.is_refusal,
                "timestamp": msg.created_at.isoformat(),
            })

    return {"session_id": session_id, "messages": history}
