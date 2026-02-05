"""Evaluation-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    """Schema for a single evaluation test case."""

    case_id: str = Field(..., description="Unique case identifier")
    question: str = Field(..., description="Test question")
    expected_answer: Optional[str] = Field(None, description="Expected answer if known")
    expected_citations: Optional[list[str]] = Field(
        None, description="Expected citation document names"
    )
    category: Optional[str] = Field(None, description="Category of the test case")
    difficulty: Optional[str] = Field(None, description="Difficulty level")


class EvalDataset(BaseModel):
    """Schema for an evaluation dataset."""

    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    cases: list[EvalCase] = Field(..., description="List of test cases")


class EvalMetrics(BaseModel):
    """Schema for evaluation metrics."""

    groundedness_score: float = Field(
        ..., ge=0, le=1, description="Percentage of claims backed by citations"
    )
    hallucination_rate: float = Field(
        ..., ge=0, le=1, description="Percentage of claims contradicting sources"
    )
    schema_compliance: float = Field(
        ..., ge=0, le=1, description="Percentage of responses matching expected structure"
    )
    tool_correctness: float = Field(
        ..., ge=0, le=1, description="Percentage of correct tool invocations"
    )
    latency_p95_ms: float = Field(
        ..., ge=0, description="95th percentile latency in milliseconds"
    )


class EvalResultResponse(BaseModel):
    """Schema for a single evaluation result."""

    case_id: str
    question: str
    expected_answer: Optional[str] = None
    actual_answer: Optional[str] = None
    citations: Optional[list[dict]] = None
    groundedness_score: Optional[float] = None
    hallucination_detected: Optional[bool] = None
    schema_compliant: Optional[bool] = None
    tool_calls_correct: Optional[bool] = None
    latency_ms: Optional[int] = None
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class EvalRunRequest(BaseModel):
    """Schema for starting an evaluation run."""

    name: str = Field(..., description="Name for this evaluation run")
    description: Optional[str] = Field(None, description="Description of the run")
    dataset_name: str = Field(..., description="Name of the dataset to use")


class EvalRunResponse(BaseModel):
    """Schema for evaluation run response."""

    eval_id: str
    name: str
    description: Optional[str] = None
    dataset_name: str
    total_cases: int
    completed_cases: int
    status: str
    error_message: Optional[str] = None
    metrics: Optional[EvalMetrics] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvalRunDetailResponse(BaseModel):
    """Schema for detailed evaluation run response with results."""

    eval_id: str
    name: str
    description: Optional[str] = None
    dataset_name: str
    total_cases: int
    completed_cases: int
    status: str
    error_message: Optional[str] = None
    metrics: Optional[EvalMetrics] = None
    results: list[EvalResultResponse] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvalRunListResponse(BaseModel):
    """Schema for evaluation run list response."""

    eval_runs: list[EvalRunResponse]
    total: int
    page: int = 1
    page_size: int = 20
