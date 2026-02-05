"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
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

    # Database
    database_url: str = "sqlite:///./data/db.sqlite"

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "ragops_documents"

    # File Storage
    upload_dir: str = "./data/uploads"

    # RAG Settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 5

    # Evaluation Settings
    eval_batch_size: int = 10
    eval_timeout_seconds: int = 30

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        # Ensure database directory exists
        db_path = self.database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
