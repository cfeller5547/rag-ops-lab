"""Main FastAPI application with Gradio UI mount."""

import logging
from contextlib import asynccontextmanager

import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import api_router
from src.config import get_settings
from src.database import init_db
from src.ui.app import create_gradio_app

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
    settings.ensure_directories()
    await init_db()
    logger.info("Database initialized")
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
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "0.1.0",
            "database": "connected",
            "vector_store": "connected",
        }
    )


@app.get("/")
async def root():
    """Root endpoint - redirects to Gradio UI."""
    return JSONResponse(
        content={
            "message": "Welcome to RAGOps Lab",
            "ui": "/ui",
            "docs": "/docs",
            "health": "/health",
        }
    )


# Mount Gradio app
gradio_app = create_gradio_app()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
