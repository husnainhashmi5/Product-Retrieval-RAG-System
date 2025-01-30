from __future__ import annotations

import re
import time
from dataclasses import dataclass

from app.ingestion.normalizer import ProductRecord, normalize_text
from app.memory.session_store import SessionStore
from app.retrieval.exact_search import find_exact_model_matches
from app.retrieval.query_parser import ParsedQuery, QueryFilters, QueryParser
from app.retrieval.vector_search import VectorSearch


@dataclass(frozen=True)
class ProductResult:
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

    @classmethod
    def from_product(cls, product: ProductRecord, *, score: float, match_type: str) -> "ProductResult":
        return cls(
            product_id=product.product_id,
            name=product.name,
            brand=product.brand,
            model=product.model,
            price=product.price,
            category=product.category,
            color=product.color,
            variation=product.variation,
            status=product.status,
            source_url=product.source_url,
            score=round(score, 4),
            match_type=match_type,
        )


@dataclass(frozen=True)
class RetrievalResult:
    products: list[ProductResult]
    applied_filters: QueryFilters
    session_id: str
    search_strategy: str
    query_intent: str
    latency_ms: float


class ProductRetriever:
    def __init__(
        self,
        *,
        products: list[ProductRecord],
        vector_search: VectorSearch | None = None,
        session_store: SessionStore | None = None,
        parser: QueryParser | None = None,
    ) -> None:
        self.products = products
        self.product_by_id = {product.product_id: product for product in products}
        self.vector_search = vector_search
        self.session_store = session_store or SessionStore()
        self.parser = parser or QueryParser()

    def search(self, query: str, session_id: str | None = None, top_k: int = 10) -> RetrievalResult:
        started = time.perf_counter()
        parsed = self.parser.parse(query)
        context = self.session_store.get_context(session_id)
        applied_filters = self._apply_context(parsed, context.to_filters())
        pool = self._candidate_pool(parsed, context.previous_result_ids)

        ranked: list[ProductResult] = []
        if parsed.exact_models:
            for model in parsed.exact_models:
                ranked.extend(
                    ProductResult.from_product(product, score=1.0, match_type="exact_model")
                    for product in self._filter_products(
                        find_exact_model_matches(self.products, model),
                        applied_filters,
                    )
                )

        should_supplement = len(parsed.exact_models) <= 1
        if should_supplement:
            local_matches = self._rank_local_matches(query, self._filter_products(pool, applied_filters))
            ranked.extend(local_matches)

        if self.vector_search and should_supplement:
            for product, score in self.vector_search.search(query, applied_filters, max(top_k, 10)):
                if self._matches_filters(product, applied_filters):
                    ranked.append(ProductResult.from_product(product, score=score, match_type="vector"))

        ranked = self._deduplicate(ranked)
        ranked = self._sort_results(ranked, parsed, applied_filters)
        if parsed.sort == "price_asc_single" and ranked:
            ranked = ranked[:1]
        else:
            ranked = ranked[:top_k]

        context.update(applied_filters, [item.product_id for item in ranked], parsed.sort)

        return RetrievalResult(
            products=ranked,
            applied_filters=applied_filters,
            session_id=session_id or "default_session",
            search_strategy=self._strategy_name(parsed, ranked),
            query_intent=parsed.intent,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )

    def _apply_context(self, parsed: ParsedQuery, previous_filters: QueryFilters) -> QueryFilters:
        if parsed.is_followup:
            return previous_filters.merged_with(parsed.filters)
        return parsed.filters

    def _candidate_pool(self, parsed: ParsedQuery, previous_result_ids: list[str]) -> list[ProductRecord]:
        if parsed.is_followup and previous_result_ids and not parsed.exact_model:
            previous = [self.product_by_id[item] for item in previous_result_ids if item in self.product_by_id]
            if previous:
                return previous
        return self.products

    def _filter_products(self, products: list[ProductRecord], filters: QueryFilters) -> list[ProductRecord]:
        return [product for product in products if self._matches_filters(product, filters)]

    def _matches_filters(self, product: ProductRecord, filters: QueryFilters) -> bool:
        if filters.status and product.status != filters.status:
            return False
        if filters.min_price is not None and (product.price is None or product.price < filters.min_price):
            return False
        if filters.max_price is not None and (product.price is None or product.price > filters.max_price):
            return False
        if filters.category and product.category != filters.category:
            return False
        if filters.brand and product.brand.lower() != filters.brand.lower():
            return False
        if filters.model and filters.model.upper() not in product.model.upper():
            return False
        if filters.color and product.color.lower() != filters.color.lower():
            return False
        if filters.variation and filters.variation.lower() not in product.variation.lower():
            return False
        return True

    def _rank_local_matches(self, query: str, products: list[ProductRecord]) -> list[ProductResult]:
        query_terms = self._terms(query)
        scored: list[ProductResult] = []
        for product in products:
            haystack = product.searchable_text().lower()
            matching_terms = sum(1 for term in query_terms if term in haystack)
            if query_terms and matching_terms == 0:
                score = 0.55
            else:
                score = 0.75 + (matching_terms / max(len(query_terms), 1)) * 0.2
            scored.append(ProductResult.from_product(product, score=score, match_type="metadata"))
        return scored

    def _terms(self, query: str) -> list[str]:
        stop_words = {
            "active",
            "show",
            "me",
            "only",
            "under",
            "below",
            "above",
            "over",
            "rs",
            "price",
            "prices",
            "in",
            "the",
            "one",
            "which",
            "is",
        }
        return [
            term
            for term in re.findall(r"[a-z0-9]+", normalize_text(query).lower())
            if term not in stop_words and not term.isdigit()
        ]

    def _deduplicate(self, results: list[ProductResult]) -> list[ProductResult]:
        best_by_id: dict[str, ProductResult] = {}
        for result in results:
            existing = best_by_id.get(result.product_id)
            if existing is None or result.score > existing.score:
                best_by_id[result.product_id] = result
        return list(best_by_id.values())

    def _sort_results(
        self,
        results: list[ProductResult],
        parsed: ParsedQuery,
        filters: QueryFilters,
    ) -> list[ProductResult]:
        if parsed.sort == "price_desc":
            return sorted(results, key=lambda item: (item.price is None, -(item.price or 0), -item.score))
        if parsed.sort == "price_asc_single" or filters.max_price is not None or filters.min_price is not None:
            return sorted(results, key=lambda item: (item.price is None, item.price or 0, -item.score))
        return sorted(results, key=lambda item: (-item.score, item.price is None, item.price or 0))

    def _strategy_name(self, parsed: ParsedQuery, ranked: list[ProductResult]) -> str:
        if not ranked:
            return "no_results"
        if parsed.exact_model and ranked[0].match_type == "exact_model":
            return "exact_model_first"
        if parsed.is_followup:
            return "context_followup"
        return "metadata_then_vector"
