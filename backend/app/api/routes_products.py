from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.api.schemas import SearchRequest, QueryResponse
from app.api.routes_chat import get_rag_system


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=QueryResponse)
async def search_products(request_body: SearchRequest, request: Request) -> QueryResponse:
    try:
        rag = get_rag_system(request)
        return await run_in_threadpool(
            rag.search_products,
            request_body.query,
            request_body.max_sources,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /search")
        raise HTTPException(status_code=500, detail="Unable to search products") from exc
