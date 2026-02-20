"""Main FastAPI application with React SPA frontend."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.api import api_router
from src.config import get_settings
from src.database import init_db

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting RAGOps Lab...")
    logger.info(f"Database: Postgres + pgvector")
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info(f"Reranking model: {settings.rerank_model}")

    await init_db()
    logger.info("Database initialized with pgvector extension")

    yield

    # Shutdown
    logger.info("Shutting down RAGOps Lab...")


# Create FastAPI app
app = FastAPI(
    title="RAGOps Lab",
    description="Agentic RAG + Evaluation + Observability Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from src.services.retrieval import RetrievalService

    try:
        retrieval = RetrievalService()
        stats = await retrieval.get_stats()

        return JSONResponse(
            content={
                "status": "healthy",
                "version": "0.1.0",
                "database": "postgres+pgvector",
                "total_documents": stats["total_documents"],
                "total_chunks": stats["total_chunks"],
                "reranking_enabled": stats["reranking_enabled"],
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
            }
        )


# Serve static frontend files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists() and (static_dir / "index.html").exists():
    # Mount assets directory for JS/CSS bundles
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve the React SPA for all non-API routes."""
        # Try to serve the exact file first
        file_path = static_dir / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Fall back to index.html for client-side routing
        return FileResponse(str(static_dir / "index.html"))
else:
    @app.get("/")
    async def root():
        """Root endpoint when no frontend is built."""
        return JSONResponse(
            content={
                "message": "Welcome to RAGOps Lab",
                "docs": "/docs",
                "health": "/health",
                "note": "Frontend not built. Run: cd frontend && npm run build, then copy dist/ to static/",
            }
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
