"""Database setup and session management for Postgres + pgvector."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from pgvector.sqlalchemy import Vector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


# Make Vector type available for models
VectorType = Vector

settings = get_settings()

# Parse database URL and handle SSL for asyncpg
database_url = settings.database_url

# asyncpg uses 'ssl' instead of 'sslmode', so we need to handle this
connect_args = {}
if "sslmode=require" in database_url or "sslmode=prefer" in database_url:
    # Remove sslmode from URL and add SSL to connect_args
    database_url = database_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
    database_url = database_url.replace("?sslmode=prefer", "").replace("&sslmode=prefer", "")
    connect_args["ssl"] = "require"

engine = create_async_engine(
    database_url,
    echo=settings.log_level == "DEBUG",
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=connect_args,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize the database, creating pgvector extension and all tables."""
    async with engine.begin() as conn:
        # Enable pgvector extension (PostgreSQL only)
        if "sqlite" not in settings.database_url:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
