from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import ClearMemoryRequest, ClearMemoryResponse, QueryRequest, QueryResponse
from app.rag.pipeline import RAGSystem


logger = logging.getLogger(__name__)
router = APIRouter()


def get_rag_system(request: Request) -> RAGSystem:
    return request.app.state.rag


@router.post("/query", response_model=QueryResponse)
async def query_products(request_body: QueryRequest, request: Request) -> QueryResponse:
    try:
        rag = get_rag_system(request)
        return rag.query_products(
            request_body.question,
            session_id=request_body.session_id,
            max_sources=request_body.max_sources,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /query")
        raise HTTPException(status_code=500, detail="Unable to process product query") from exc


@router.post("/clear_memory", response_model=ClearMemoryResponse)
async def clear_memory(request_body: ClearMemoryRequest, request: Request) -> ClearMemoryResponse:
    try:
        rag = get_rag_system(request)
        rag.clear_memory(request_body.session_id)
        return ClearMemoryResponse(
            message="Memory cleared successfully",
            session_id=request_body.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /clear_memory")
        raise HTTPException(status_code=500, detail="Unable to clear session memory") from exc
