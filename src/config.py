"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Database - Postgres
    database_url: str = "postgresql+asyncpg://localhost/ragops"

    # File Storage
    max_file_size_mb: int = 10
    store_raw_files: bool = True

    # RAG Settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 10
    rerank_top_k: int = 5

    # Reranking
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Evaluation Settings
    eval_batch_size: int = 10
    eval_timeout_seconds: int = 30

    # Observability
    enable_telemetry: bool = True
    otel_service_name: str = "ragops-lab"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
