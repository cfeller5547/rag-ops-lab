"""Evaluation service for running test suites and computing metrics."""

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from sqlalchemy import select

from src.config import get_settings
from src.database import get_db_context
from src.models.eval_run import EvalResult, EvalRun
from src.schemas.eval import EvalCase, EvalDataset
from src.services.agent import RAGAgent
from src.services.tracing import TracingService

logger = logging.getLogger(__name__)
settings = get_settings()


class EvaluationService:
    """Service for running evaluations and computing metrics."""

    def __init__(self):
        self.batch_size = settings.eval_batch_size
        self.timeout = settings.eval_timeout_seconds

    async def run_evaluation(self, eval_run_id: int) -> None:
        """Run an evaluation asynchronously."""
        async with get_db_context() as db:
            # Get eval run
            result = await db.execute(
                select(EvalRun).where(EvalRun.id == eval_run_id)
            )
            eval_run = result.scalar_one_or_none()

            if not eval_run:
                logger.error(f"Eval run {eval_run_id} not found")
                return

            try:
                # Update status
                eval_run.status = "running"
                eval_run.started_at = datetime.utcnow()
                await db.commit()

                # Load dataset
                dataset = await self._load_dataset(eval_run.dataset_name)

                # Run evaluation cases
                latencies = []
                groundedness_scores = []
                hallucination_count = 0
                schema_compliant_count = 0
                tool_correct_count = 0
                total_cases = len(dataset.cases)

                agent = RAGAgent()

                for i, case in enumerate(dataset.cases):
                    # Check if cancelled
                    await db.refresh(eval_run)
                    if eval_run.status == "cancelled":
                        logger.info(f"Eval run {eval_run_id} was cancelled")
                        return

                    try:
                        result_data = await self._run_single_case(agent, case)

                        # Create result record
                        eval_result = EvalResult(
                            eval_run_id=eval_run.id,
                            case_id=case.case_id,
                            question=case.question,
                            expected_answer=case.expected_answer,
                            actual_answer=result_data["answer"],
                            citations=json.dumps(result_data["citations"]),
                            groundedness_score=result_data["groundedness"],
                            hallucination_detected=result_data["hallucination"],
                            schema_compliant=result_data["schema_compliant"],
                            tool_calls_correct=result_data["tool_correct"],
                            latency_ms=result_data["latency_ms"],
                            status="passed" if result_data["passed"] else "failed",
                        )
                        db.add(eval_result)

                        # Aggregate metrics
                        latencies.append(result_data["latency_ms"])
                        groundedness_scores.append(result_data["groundedness"])
                        if result_data["hallucination"]:
                            hallucination_count += 1
                        if result_data["schema_compliant"]:
                            schema_compliant_count += 1
                        if result_data["tool_correct"]:
                            tool_correct_count += 1

                    except Exception as e:
                        logger.error(f"Case {case.case_id} failed: {e}")
                        eval_result = EvalResult(
                            eval_run_id=eval_run.id,
                            case_id=case.case_id,
                            question=case.question,
                            expected_answer=case.expected_answer,
                            status="error",
                            error_message=str(e),
                        )
                        db.add(eval_result)

                    eval_run.completed_cases = i + 1
                    await db.commit()

                # Calculate final metrics
                if latencies:
                    eval_run.latency_p95_ms = float(np.percentile(latencies, 95))
                if groundedness_scores:
                    eval_run.groundedness_score = float(np.mean(groundedness_scores))
                eval_run.hallucination_rate = hallucination_count / total_cases if total_cases > 0 else 0
                eval_run.schema_compliance = schema_compliant_count / total_cases if total_cases > 0 else 0
                eval_run.tool_correctness = tool_correct_count / total_cases if total_cases > 0 else 0

                eval_run.status = "completed"
                eval_run.completed_at = datetime.utcnow()
                await db.commit()

                logger.info(f"Evaluation {eval_run_id} completed")

            except Exception as e:
                logger.error(f"Evaluation {eval_run_id} failed: {e}")
                eval_run.status = "failed"
                eval_run.error_message = str(e)
                eval_run.completed_at = datetime.utcnow()
                await db.commit()

    async def _load_dataset(self, dataset_name: str) -> EvalDataset:
        """Load an evaluation dataset."""
        dataset_path = Path("eval_datasets") / f"{dataset_name}.json"
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_name}")

        with open(dataset_path) as f:
            data = json.load(f)

        return EvalDataset(**data)

    async def _run_single_case(self, agent: RAGAgent, case: EvalCase) -> dict:
        """Run a single evaluation case and compute metrics."""
        run_id = str(uuid.uuid4())
        session_id = f"eval_{run_id}"
        tracer = TracingService(run_id=run_id, session_id=session_id)

        start_time = time.time()

        try:
            response = await agent.chat(
                message=case.question,
                session_id=session_id,
                tracer=tracer,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            # Compute metrics
            if response.is_refusal:
                groundedness = 1.0  # Correct refusal = perfectly grounded
            else:
                groundedness = self._compute_groundedness(response.content, response.citations)
            hallucination = self._detect_hallucination(
                response.content, response.citations, case.expected_answer
            )
            schema_compliant = self._check_schema_compliance(response)
            # Tool is correct if search_corpus was called for a non-refusal response,
            # or if the response is a refusal (declining without search is also valid).
            tool_correct = "search_corpus" in response.tools_called or response.is_refusal

            # Determine if passed
            passed = (
                groundedness >= 0.5
                and not hallucination
                and schema_compliant
                and latency_ms < 4000
            )

            return {
                "answer": response.content,
                "citations": [c.model_dump() for c in response.citations],
                "groundedness": groundedness,
                "hallucination": hallucination,
                "schema_compliant": schema_compliant,
                "tool_correct": tool_correct,
                "latency_ms": latency_ms,
                "passed": passed,
            }

        except Exception as e:
            logger.error(f"Case execution failed: {e}")
            raise

    def _compute_groundedness(self, answer: str, citations: list) -> float:
        """Compute groundedness score (0-1) based on citation coverage of claims."""
        import re

        if not answer:
            return 0.0

        if not citations:
            return 0.0

        # Split into sentences (skip very short fragments under 10 chars)
        sentences = [
            s.strip()
            for s in re.split(r'(?<=[.!?])\s+', answer)
            if s.strip() and len(s.strip()) > 10
        ]

        if not sentences:
            # Very short answer — check if it has any citation marker
            if re.search(r'\[\d+\]', answer):
                return 0.8
            return 0.3

        # Count sentences that contain at least one citation marker [N]
        citation_pattern = re.compile(r'\[\d+\]')
        cited_sentences = sum(1 for s in sentences if citation_pattern.search(s))

        # Recognize transitional/introductory sentences that don't need citations
        transitional_pattern = re.compile(
            r'^(here|in summary|based on|according to|overall|to summarize|'
            r'in conclusion|additionally|furthermore|the following)',
            re.IGNORECASE,
        )
        transitional_count = sum(
            1 for s in sentences if transitional_pattern.match(s)
        )

        # Effective sentences that SHOULD have citations
        claimable_sentences = max(len(sentences) - transitional_count, 1)

        # Coverage ratio
        coverage = min(cited_sentences / claimable_sentences, 1.0)

        # Score: 0.4 base (has citations object) + 0.6 scaled by coverage
        return 0.4 + (coverage * 0.6)

    def _detect_hallucination(
        self,
        answer: str,
        citations: list,
        expected_answer: Optional[str],
    ) -> bool:
        """Detect if response contains hallucination."""
        if not answer:
            return False

        # If response is a refusal, it's not hallucination
        if answer.lower().startswith("i cannot answer"):
            return False

        # If no citations but claims to have information, likely hallucination
        if not citations and len(answer) > 100:
            citation_markers = ["[1]", "[2]", "[3]", "[4]", "[5]"]
            if not any(marker in answer for marker in citation_markers):
                # Check if making factual claims without sources
                claim_indicators = ["is", "are", "was", "were", "the", "this"]
                claim_count = sum(
                    1 for indicator in claim_indicators
                    if f" {indicator} " in answer.lower()
                )
                if claim_count > 3:
                    return True

        return False

    def _check_schema_compliance(self, response) -> bool:
        """Check if response follows expected schema."""
        # Check basic requirements
        if not response.content:
            return False

        # If it's a refusal, should have refusal flag
        if response.content.lower().startswith("i cannot answer"):
            return response.is_refusal

        # Non-refusal should have citations
        if not response.is_refusal and not response.citations:
            return False

        return True

    async def compare_runs(self, eval_id_a: str, eval_id_b: str) -> dict:
        """Compare two evaluation runs."""
        async with get_db_context() as db:
            # Get both runs
            result_a = await db.execute(
                select(EvalRun).where(EvalRun.eval_id == eval_id_a)
            )
            run_a = result_a.scalar_one_or_none()

            result_b = await db.execute(
                select(EvalRun).where(EvalRun.eval_id == eval_id_b)
            )
            run_b = result_b.scalar_one_or_none()

            if not run_a or not run_b:
                raise ValueError("One or both eval runs not found")

            return {
                "run_a": {
                    "eval_id": run_a.eval_id,
                    "name": run_a.name,
                    "groundedness": run_a.groundedness_score,
                    "hallucination_rate": run_a.hallucination_rate,
                    "schema_compliance": run_a.schema_compliance,
                    "tool_correctness": run_a.tool_correctness,
                    "latency_p95_ms": run_a.latency_p95_ms,
                },
                "run_b": {
                    "eval_id": run_b.eval_id,
                    "name": run_b.name,
                    "groundedness": run_b.groundedness_score,
                    "hallucination_rate": run_b.hallucination_rate,
                    "schema_compliance": run_b.schema_compliance,
                    "tool_correctness": run_b.tool_correctness,
                    "latency_p95_ms": run_b.latency_p95_ms,
                },
                "diff": {
                    "groundedness": (run_b.groundedness_score or 0) - (run_a.groundedness_score or 0),
                    "hallucination_rate": (run_b.hallucination_rate or 0) - (run_a.hallucination_rate or 0),
                    "schema_compliance": (run_b.schema_compliance or 0) - (run_a.schema_compliance or 0),
                    "tool_correctness": (run_b.tool_correctness or 0) - (run_a.tool_correctness or 0),
                    "latency_p95_ms": (run_b.latency_p95_ms or 0) - (run_a.latency_p95_ms or 0),
                },
            }
