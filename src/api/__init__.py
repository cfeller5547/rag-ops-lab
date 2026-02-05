"""FastAPI API routes for RAGOps Lab."""

from fastapi import APIRouter

from src.api.chat import router as chat_router
from src.api.documents import router as documents_router
from src.api.evals import router as evals_router
from src.api.traces import router as traces_router

api_router = APIRouter()

api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(evals_router, prefix="/evals", tags=["evaluations"])
api_router.include_router(traces_router, prefix="/traces", tags=["traces"])

__all__ = ["api_router"]
