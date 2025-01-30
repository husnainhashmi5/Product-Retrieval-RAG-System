from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    session_id: str | None = Field(default=None, max_length=120)
    max_sources: int = Field(default=10, ge=1, le=25)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    max_sources: int = Field(default=10, ge=1, le=25)


class ClearMemoryRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=120)


class AppliedFilters(BaseModel):
    min_price: int | None = None
    max_price: int | None = None
    category: str | None = None
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    variation: str | None = None
    status: str | None = None


class ProductResponse(BaseModel):
    product_id: str
    name: str
    brand: str
    model: str
    price: int | None
    category: str
    color: str
    variation: str
    status: str
    source_url: str
    score: float
    match_type: str


class QueryResponse(BaseModel):
    answer: str
    products: list[ProductResponse]
    applied_filters: AppliedFilters
    session_id: str
    search_strategy: str
    query_intent: str
    used_web_search: bool = False
    latency_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClearMemoryResponse(BaseModel):
    message: str
    session_id: str


class HealthResponse(BaseModel):
    status: str
    message: str
