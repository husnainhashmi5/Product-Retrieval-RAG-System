from __future__ import annotations

import logging
from typing import Protocol

from app.core.config import Settings
from app.ingestion.normalizer import ProductRecord
from app.retrieval.query_parser import QueryFilters


logger = logging.getLogger(__name__)


class VectorSearch(Protocol):
    def search(self, query: str, filters: QueryFilters, top_k: int) -> list[tuple[ProductRecord, float]]:
        ...


def pinecone_filter_from_query(filters: QueryFilters) -> dict:
    pinecone_filter: dict = {}
    if filters.status:
        pinecone_filter["status"] = {"$eq": filters.status}
    if filters.category:
        pinecone_filter["category"] = {"$eq": filters.category}
    if filters.brand:
        pinecone_filter["brand"] = {"$eq": filters.brand}
    if filters.model:
        pinecone_filter["model"] = {"$eq": filters.model}
    if filters.color:
        pinecone_filter["color"] = {"$eq": filters.color}
    if filters.variation:
        pinecone_filter["variation"] = {"$eq": filters.variation}
    if filters.min_price is not None or filters.max_price is not None:
        price_filter = {}
        if filters.min_price is not None:
            price_filter["$gte"] = filters.min_price
        if filters.max_price is not None:
            price_filter["$lte"] = filters.max_price
        pinecone_filter["price"] = price_filter
    return pinecone_filter


class PineconeVectorSearch:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._vectorstore = None

    def search(self, query: str, filters: QueryFilters, top_k: int) -> list[tuple[ProductRecord, float]]:
        try:
            vectorstore = self._get_vectorstore()
            pinecone_filter = pinecone_filter_from_query(filters)
            docs = vectorstore.similarity_search_with_score(
                query,
                k=top_k,
                filter=pinecone_filter,
            )
            results = []
            for doc, score in docs:
                product = self._product_from_metadata(doc.metadata or {})
                if product:
                    results.append((product, float(score)))
            return results
        except Exception as exc:
            logger.warning("Vector search unavailable: %s", exc)
            return []

    def _get_vectorstore(self):
        if self._vectorstore is None:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            from langchain_pinecone import PineconeVectorStore

            embeddings = GoogleGenerativeAIEmbeddings(
                model=self.settings.embedding_model,
                google_api_key=self.settings.google_api_key,
                task_type="RETRIEVAL_QUERY",
            )
            self._vectorstore = PineconeVectorStore(
                index_name=self.settings.pinecone_index_name,
                embedding=embeddings,
            )
        return self._vectorstore

    def _product_from_metadata(self, metadata: dict) -> ProductRecord | None:
        product_id = metadata.get("product_id")
        name = metadata.get("name")
        if not product_id or not name:
            return None
        price = metadata.get("price")
        return ProductRecord(
            product_id=str(product_id),
            name=str(name),
            brand=str(metadata.get("brand") or ""),
            model=str(metadata.get("model") or ""),
            category=str(metadata.get("category") or ""),
            price=int(price) if price is not None else None,
            color=str(metadata.get("color") or ""),
            variation=str(metadata.get("variation") or ""),
            status=str(metadata.get("status") or "unknown"),
            source_url=str(metadata.get("source_url") or ""),
            source_row=str(metadata.get("source_row") or ""),
            raw=dict(metadata),
        )
