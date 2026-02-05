"""Evaluation API endpoints."""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import get_settings
from src.database import get_db
from src.models.eval_run import EvalResult, EvalRun
from src.schemas.eval import (
    EvalDataset,
    EvalMetrics,
    EvalRunDetailResponse,
    EvalRunListResponse,
    EvalRunRequest,
    EvalRunResponse,
    EvalResultResponse,
)
from src.services.evaluation import EvaluationService

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def _build_metrics(eval_run: EvalRun) -> Optional[EvalMetrics]:
    """Build metrics object from eval run."""
    if eval_run.groundedness_score is None:
        return None
    return EvalMetrics(
        groundedness_score=eval_run.groundedness_score or 0.0,
        hallucination_rate=eval_run.hallucination_rate or 0.0,
        schema_compliance=eval_run.schema_compliance or 0.0,
        tool_correctness=eval_run.tool_correctness or 0.0,
        latency_p95_ms=eval_run.latency_p95_ms or 0.0,
    )


def _eval_run_to_response(eval_run: EvalRun) -> EvalRunResponse:
    """Convert EvalRun model to response schema."""
    return EvalRunResponse(
        eval_id=eval_run.eval_id,
        name=eval_run.name,
        description=eval_run.description,
        dataset_name=eval_run.dataset_name,
        total_cases=eval_run.total_cases,
        completed_cases=eval_run.completed_cases,
        status=eval_run.status,
        error_message=eval_run.error_message,
        metrics=_build_metrics(eval_run),
        started_at=eval_run.started_at,
        completed_at=eval_run.completed_at,
        created_at=eval_run.created_at,
    )


@router.get("", response_model=EvalRunListResponse)
async def list_eval_runs(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> EvalRunListResponse:
    """List all evaluation runs with pagination."""
    offset = (page - 1) * page_size

    query = select(EvalRun).order_by(EvalRun.created_at.desc())
    if status_filter:
        query = query.where(EvalRun.status == status_filter)

    # Get total count
    count_query = select(func.count(EvalRun.id))
    if status_filter:
        count_query = count_query.where(EvalRun.status == status_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    eval_runs = result.scalars().all()

    return EvalRunListResponse(
        eval_runs=[_eval_run_to_response(run) for run in eval_runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/datasets")
async def list_datasets() -> list[dict]:
    """List available evaluation datasets."""
    datasets_dir = Path("eval_datasets")
    datasets = []

    if datasets_dir.exists():
        for file_path in datasets_dir.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                datasets.append({
                    "name": file_path.stem,
                    "filename": file_path.name,
                    "description": data.get("description", ""),
                    "case_count": len(data.get("cases", [])),
                })
            except Exception as e:
                logger.warning(f"Failed to read dataset {file_path}: {e}")

    return datasets


@router.post("", response_model=EvalRunResponse, status_code=status.HTTP_201_CREATED)
async def create_eval_run(
    request: EvalRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> EvalRunResponse:
    """Create and start a new evaluation run."""
    # Load dataset
    dataset_path = Path("eval_datasets") / f"{request.dataset_name}.json"
    if not dataset_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{request.dataset_name}' not found",
        )

    try:
        with open(dataset_path) as f:
            dataset_data = json.load(f)
        dataset = EvalDataset(**dataset_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load dataset: {e}",
        )

    # Create eval run record
    import uuid
    eval_run = EvalRun(
        eval_id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        dataset_name=request.dataset_name,
        total_cases=len(dataset.cases),
        status="pending",
    )
    db.add(eval_run)
    await db.commit()
    await db.refresh(eval_run)

    # Start evaluation in background
    eval_service = EvaluationService()
    background_tasks.add_task(eval_service.run_evaluation, eval_run.id)

    return _eval_run_to_response(eval_run)


@router.get("/{eval_id}", response_model=EvalRunDetailResponse)
async def get_eval_run(
    eval_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvalRunDetailResponse:
    """Get an evaluation run by ID with results."""
    result = await db.execute(
        select(EvalRun)
        .where(EvalRun.eval_id == eval_id)
        .options(selectinload(EvalRun.results))
    )
    eval_run = result.scalar_one_or_none()

    if not eval_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{eval_id}' not found",
        )

    return EvalRunDetailResponse(
        eval_id=eval_run.eval_id,
        name=eval_run.name,
        description=eval_run.description,
        dataset_name=eval_run.dataset_name,
        total_cases=eval_run.total_cases,
        completed_cases=eval_run.completed_cases,
        status=eval_run.status,
        error_message=eval_run.error_message,
        metrics=_build_metrics(eval_run),
        results=[
            EvalResultResponse(
                case_id=r.case_id,
                question=r.question,
                expected_answer=r.expected_answer,
                actual_answer=r.actual_answer,
                citations=json.loads(r.citations) if r.citations else None,
                groundedness_score=r.groundedness_score,
                hallucination_detected=r.hallucination_detected,
                schema_compliant=r.schema_compliant,
                tool_calls_correct=r.tool_calls_correct,
                latency_ms=r.latency_ms,
                status=r.status,
                error_message=r.error_message,
            )
            for r in eval_run.results
        ],
        started_at=eval_run.started_at,
        completed_at=eval_run.completed_at,
        created_at=eval_run.created_at,
    )


@router.delete("/{eval_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_eval_run(
    eval_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an evaluation run."""
    result = await db.execute(
        select(EvalRun).where(EvalRun.eval_id == eval_id)
    )
    eval_run = result.scalar_one_or_none()

    if not eval_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{eval_id}' not found",
        )

    await db.delete(eval_run)
    await db.commit()


@router.post("/{eval_id}/cancel")
async def cancel_eval_run(
    eval_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvalRunResponse:
    """Cancel a running evaluation."""
    result = await db.execute(
        select(EvalRun).where(EvalRun.eval_id == eval_id)
    )
    eval_run = result.scalar_one_or_none()

    if not eval_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{eval_id}' not found",
        )

    if eval_run.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel evaluation in status '{eval_run.status}'",
        )

    eval_run.status = "cancelled"
    await db.commit()
    await db.refresh(eval_run)

    return _eval_run_to_response(eval_run)
