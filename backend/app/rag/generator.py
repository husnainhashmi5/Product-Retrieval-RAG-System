from __future__ import annotations

from app.retrieval.product_retriever import ProductResult
from app.retrieval.query_parser import QueryFilters


class AnswerGenerator:
    def generate(self, products: list[ProductResult], filters: QueryFilters) -> str:
        if not products:
            return "I couldn't find matching products for those filters."

        if len(products) == 1:
            product = products[0]
            return (
                f"I found 1 matching product: {product.name}"
                f"{f' ({product.model})' if product.model else ''}"
                f"{f' for Rs {product.price:,}' if product.price is not None else ''}."
            )

        filter_text = self._filter_summary(filters)
        return f"Here are {len(products)} matching products{filter_text}."

    def _filter_summary(self, filters: QueryFilters) -> str:
        parts = []
        if filters.brand:
            parts.append(filters.brand)
        if filters.category:
            parts.append(filters.category)
        if filters.color:
            parts.append(filters.color)
        if filters.max_price is not None:
            parts.append(f"under Rs {filters.max_price:,}")
        if filters.min_price is not None:
            parts.append(f"above Rs {filters.min_price:,}")
        if not parts:
            return ""
        return " for " + ", ".join(parts)
