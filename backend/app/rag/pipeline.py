from __future__ import annotations

from app.api.schemas import AppliedFilters, ProductResponse, QueryResponse
from app.core.config import Settings
from app.ingestion.csv_loader import load_products_from_csv
from app.ingestion.normalizer import ProductRecord
from app.memory.session_store import SessionStore
from app.rag.generator import AnswerGenerator
from app.retrieval.product_retriever import ProductRetriever, RetrievalResult
from app.retrieval.vector_search import PineconeVectorSearch, VectorSearch


class RAGSystem:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        products: list[ProductRecord] | None = None,
        vector_search: VectorSearch | None = None,
        session_store: SessionStore | None = None,
        answer_generator: AnswerGenerator | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.session_store = session_store or SessionStore()
        loaded_products = products if products is not None else self._load_products()
        active_products = [product for product in loaded_products if product.status == "active"]
        self.vector_search = vector_search or self._build_vector_search()
        self.retriever = ProductRetriever(
            products=active_products,
            vector_search=self.vector_search,
            session_store=self.session_store,
        )
        self.answer_generator = answer_generator or AnswerGenerator()

    def query_products(self, question: str, session_id: str | None = None, max_sources: int | None = None) -> QueryResponse:
        result = self.retriever.search(
            question,
            session_id=session_id,
            top_k=max_sources or self.settings.max_sources,
        )
        return self._response_from_retrieval(result)

    def search_products(self, query: str, max_sources: int | None = None) -> QueryResponse:
        result = self.retriever.search(
            query,
            session_id=None,
            top_k=max_sources or self.settings.max_sources,
        )
        return self._response_from_retrieval(result)

    def clear_memory(self, session_id: str) -> None:
        self.session_store.clear_session(session_id)

    def _load_products(self) -> list[ProductRecord]:
        report = load_products_from_csv(
            self.settings.resolved_csv_path(),
            active_only=self.settings.active_only_indexing,
        )
        return report.products

    def _build_vector_search(self) -> VectorSearch | None:
        if not (
            self.settings.require_external_services
            and self.settings.pinecone_api_key
            and self.settings.pinecone_index_name
            and self.settings.google_api_key
        ):
            return None
        return PineconeVectorSearch(self.settings)

    def _response_from_retrieval(self, result: RetrievalResult) -> QueryResponse:
        answer = self.answer_generator.generate(result.products, result.applied_filters)
        return QueryResponse(
            answer=answer,
            products=[ProductResponse(**product.__dict__) for product in result.products],
            applied_filters=AppliedFilters(**result.applied_filters.to_dict(exclude_none=False)),
            session_id=result.session_id,
            search_strategy=result.search_strategy,
            query_intent=result.query_intent,
            used_web_search=False,
            latency_ms=result.latency_ms,
            metadata={"result_count": len(result.products)},
        )
