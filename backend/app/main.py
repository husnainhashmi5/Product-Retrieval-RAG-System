from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_products import router as products_router
from app.api.schemas import HealthResponse
from app.core.config import Settings
from app.core.logging import configure_logging
from app.rag.pipeline import RAGSystem


def create_app(settings: Settings | None = None, rag_system: RAGSystem | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    configure_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        settings.validate()
        application.state.settings = settings
        application.state.rag = rag_system or RAGSystem(settings=settings)
        yield

    application = FastAPI(
        title="Product Retrieval RAG API",
        version="2.0.0",
        lifespan=lifespan,
    )
    application.state.settings = settings
    if rag_system is not None:
        application.state.rag = rag_system
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
    application.include_router(chat_router)
    application.include_router(products_router)

    @application.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        return HealthResponse(status="healthy", message="Product Retrieval RAG API is running")

    return application


app = create_app()
