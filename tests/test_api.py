"""Basic API tests for RAGOps Lab."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["ui"] == "/ui"


def test_documents_list_empty(client):
    """Test empty documents list."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data


def test_evals_list_empty(client):
    """Test empty evals list."""
    response = client.get("/api/evals")
    assert response.status_code == 200
    data = response.json()
    assert "eval_runs" in data
    assert "total" in data


def test_traces_list_empty(client):
    """Test empty traces list."""
    response = client.get("/api/traces")
    assert response.status_code == 200
    data = response.json()
    assert "traces" in data
    assert "total" in data


def test_datasets_list(client):
    """Test datasets list."""
    response = client.get("/api/evals/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
