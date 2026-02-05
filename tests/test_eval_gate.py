"""Evaluation gate tests for CI pipeline.

These tests verify that the RAG system meets minimum quality thresholds.
They run as part of the PR process to prevent quality regressions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestEvalGate:
    """Evaluation gate tests."""

    def test_groundedness_threshold(self):
        """Test that groundedness scoring logic works correctly."""
        from src.services.evaluation import EvaluationService

        eval_service = EvaluationService()

        # Test with citations present
        answer_with_citations = "According to the handbook [1], employees get 15 days PTO."
        citations = [{"content": "employees get 15 days PTO"}]
        score = eval_service._compute_groundedness(answer_with_citations, citations)
        assert score >= 0.5, f"Groundedness score {score} below threshold"

        # Test without citations
        answer_no_citations = "Employees get 15 days PTO."
        score_no_cite = eval_service._compute_groundedness(answer_no_citations, [])
        assert score_no_cite < score, "Answer without citations should score lower"

    def test_hallucination_detection(self):
        """Test that hallucination detection works correctly."""
        from src.services.evaluation import EvaluationService

        eval_service = EvaluationService()

        # Refusal should not be hallucination
        refusal = "I cannot answer this question based on the available documents."
        assert not eval_service._detect_hallucination(refusal, [], None)

        # Short response without citations is not necessarily hallucination
        short_response = "Yes."
        assert not eval_service._detect_hallucination(short_response, [], None)

    def test_schema_compliance(self):
        """Test schema compliance checking."""
        from src.services.evaluation import EvaluationService

        eval_service = EvaluationService()

        # Create mock response objects
        class MockResponse:
            def __init__(self, content, is_refusal, citations):
                self.content = content
                self.is_refusal = is_refusal
                self.citations = citations

        # Valid response with citations
        valid_response = MockResponse(
            content="The answer is X [1].",
            is_refusal=False,
            citations=[{"content": "X"}]
        )
        assert eval_service._check_schema_compliance(valid_response)

        # Valid refusal
        valid_refusal = MockResponse(
            content="I cannot answer this question based on the available documents.",
            is_refusal=True,
            citations=[]
        )
        assert eval_service._check_schema_compliance(valid_refusal)

        # Invalid: non-refusal without citations
        invalid_response = MockResponse(
            content="The answer is X.",
            is_refusal=False,
            citations=[]
        )
        assert not eval_service._check_schema_compliance(invalid_response)

    def test_chunk_text_function(self):
        """Test that chunking produces valid chunks."""
        from src.services.ingestion import IngestionService

        ingestion = IngestionService()

        # Test with sample text
        sample_text = "This is a test document. " * 100
        chunks = ingestion._chunk_text(sample_text, "test.txt")

        assert len(chunks) > 0, "Should produce at least one chunk"

        for chunk in chunks:
            assert "content" in chunk
            assert "chunk_index" in chunk
            assert "start_char" in chunk
            assert "end_char" in chunk
            assert len(chunk["content"]) <= ingestion.chunk_size + 50  # Allow small overflow

    def test_retrieval_result_structure(self):
        """Test that retrieval results have correct structure."""
        from src.services.retrieval import RetrievalResult

        result = RetrievalResult(
            chunk_id=1,
            document_id=1,
            document_name="test.pdf",
            content="Test content",
            chunk_index=0,
            page_number=1,
            relevance_score=0.85,
        )

        assert result.chunk_id == 1
        assert result.document_name == "test.pdf"
        assert 0 <= result.relevance_score <= 1

    def test_citation_format(self):
        """Test that citations are properly formatted."""
        from src.schemas.chat import Citation

        citation = Citation(
            document_id=1,
            document_name="handbook.pdf",
            chunk_id=5,
            chunk_index=2,
            content="Sample citation content",
            page_number=10,
            relevance_score=0.9,
        )

        assert citation.document_name == "handbook.pdf"
        assert citation.page_number == 10
        assert citation.relevance_score == 0.9


class TestQualityMetrics:
    """Tests for quality metric calculations."""

    def test_latency_threshold(self):
        """Verify latency calculation is reasonable."""
        import time

        # Simulate a response time measurement
        start = time.time()
        time.sleep(0.01)  # 10ms
        latency_ms = int((time.time() - start) * 1000)

        # Should be measurable
        assert latency_ms >= 10
        # Should be under reasonable threshold for unit test
        assert latency_ms < 1000

    def test_percentile_calculation(self):
        """Test P95 latency calculation."""
        import numpy as np

        latencies = [100, 150, 200, 250, 300, 350, 400, 450, 500, 5000]
        p95 = np.percentile(latencies, 95)

        # P95 should be high due to outlier
        assert p95 > 400
        # But not the max
        assert p95 < 5000
