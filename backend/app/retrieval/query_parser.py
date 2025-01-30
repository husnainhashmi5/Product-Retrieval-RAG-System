from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.ingestion.normalizer import COLOR_MAP, KNOWN_BRANDS, normalize_category, normalize_color, normalize_model, parse_price


CATEGORY_KEYWORDS = {
    "washing machine": ("washing machine", "washing machines", "washer", "washers"),
    "refrigerator": ("refrigerator", "refrigerators", "fridge", "fridges"),
    "microwave": ("microwave", "microwaves", "oven", "ovens"),
    "television": ("television", "televisions", "tv", "tvs", "led", "qled", "oled"),
    "phone": ("phone", "phones", "mobile", "mobiles", "smartphone", "smartphones"),
    "laptop": ("laptop", "laptops", "notebook", "notebooks"),
    "hob": ("hob", "hobs", "burner", "burners"),
    "freezer": ("freezer", "freezers"),
    "air conditioner": ("air conditioner", "air conditioners", "ac"),
}


@dataclass(frozen=True)
class QueryFilters:
    min_price: int | None = None
    max_price: int | None = None
    category: str | None = None
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    variation: str | None = None
    status: str | None = "active"

    def merged_with(self, current: "QueryFilters") -> "QueryFilters":
        return QueryFilters(
            min_price=current.min_price if current.min_price is not None else self.min_price,
            max_price=current.max_price if current.max_price is not None else self.max_price,
            category=current.category if current.category is not None else self.category,
            brand=current.brand if current.brand is not None else self.brand,
            model=current.model if current.model is not None else self.model,
            color=current.color if current.color is not None else self.color,
            variation=current.variation if current.variation is not None else self.variation,
            status=current.status if current.status is not None else self.status,
        )

    def to_dict(self, *, exclude_none: bool = True) -> dict[str, Any]:
        payload = {
            "min_price": self.min_price,
            "max_price": self.max_price,
            "category": self.category,
            "brand": self.brand,
            "model": self.model,
            "color": self.color,
            "variation": self.variation,
            "status": self.status,
        }
        if exclude_none:
            return {key: value for key, value in payload.items() if value is not None}
        return payload


@dataclass(frozen=True)
class ParsedQuery:
    original_query: str
    normalized_query: str
    filters: QueryFilters
    exact_model: str | None
    exact_models: list[str]
    intent: str
    sort: str | None
    is_followup: bool


class QueryParser:
    MODEL_PATTERN = re.compile(
        r"\b[A-Za-z]{1,6}-\d{1,4}[A-Za-z0-9]*(?:-[A-Za-z0-9]+)*(?:/[A-Za-z0-9]+)*\b"
        r"|\b[A-Za-z]{1,6}\d{1,4}(?:-[A-Za-z0-9]+)+(?:/[A-Za-z0-9]+)*\b"
        r"|\b[A-Za-z]{2,6}\d{2,}[A-Za-z0-9]*\b"
    )

    def parse(self, query: str) -> ParsedQuery:
        normalized_query = re.sub(r"\s+", " ", query).strip()
        query_lower = normalized_query.lower()
        min_price, max_price = self._parse_price_filters(query_lower)
        exact_models = self._parse_models(normalized_query)
        exact_model = exact_models[0] if exact_models else None
        category = self._parse_category(query_lower)
        brand = self._parse_brand(query_lower)
        color = normalize_color("", query_lower) or None
        status = self._parse_status(query_lower)
        sort = self._parse_sort(query_lower)
        intent = self._parse_intent(query_lower, min_price, max_price, exact_model, sort)

        filters = QueryFilters(
            min_price=min_price,
            max_price=max_price,
            category=category,
            brand=brand,
            model=exact_model if len(exact_models) <= 1 else None,
            color=color,
            status=status,
        )

        return ParsedQuery(
            original_query=query,
            normalized_query=normalized_query,
            filters=filters,
            exact_model=exact_model,
            exact_models=exact_models,
            intent=intent,
            sort=sort,
            is_followup=self._is_followup(query_lower, filters, sort),
        )

    def _parse_price_filters(self, query_lower: str) -> tuple[int | None, int | None]:
        between = re.search(
            r"between\s+(?:rs\.?\s*)?([\d,]+(?:k)?)\s+(?:and|to|-)\s+(?:rs\.?\s*)?([\d,]+(?:k)?)",
            query_lower,
        )
        if between:
            return parse_price(between.group(1)), parse_price(between.group(2))

        max_price = None
        min_price = None
        max_match = re.search(
            r"(?:under|below|less than|up to|max(?:imum)?|budget)\s+(?:rs\.?\s*)?([\d,]+(?:k)?)",
            query_lower,
        )
        min_match = re.search(
            r"(?:above|over|more than|min(?:imum)?)\s+(?:rs\.?\s*)?([\d,]+(?:k)?)",
            query_lower,
        )
        if max_match:
            max_price = parse_price(max_match.group(1))
        if min_match:
            min_price = parse_price(min_match.group(1))
        return min_price, max_price

    def _parse_models(self, query: str) -> list[str]:
        candidates = [normalize_model(match.group(0)) for match in self.MODEL_PATTERN.finditer(query)]
        candidates = [candidate for candidate in candidates if candidate and not candidate.startswith("RS-")]
        unique = []
        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)
        return unique

    def _parse_category(self, query_lower: str) -> str | None:
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(re.search(rf"\b{re.escape(keyword)}\b", query_lower) for keyword in keywords):
                return category
        normalized = normalize_category(query_lower)
        return normalized if normalized != query_lower else None

    def _parse_brand(self, query_lower: str) -> str | None:
        for raw, brand in KNOWN_BRANDS.items():
            if re.search(rf"\b{re.escape(raw)}\b", query_lower):
                return brand
        hp_match = re.search(r"\bhp\b", query_lower)
        if hp_match:
            return "HP"
        return None

    def _parse_status(self, query_lower: str) -> str | None:
        if re.search(r"\b(inactive|disabled|discontinued|out of stock)\b", query_lower):
            return "inactive"
        return "active"

    def _parse_sort(self, query_lower: str) -> str | None:
        if re.search(r"\b(cheapest|lowest price|least expensive)\b", query_lower):
            return "price_asc_single"
        if re.search(r"\b(expensive|highest price|premium)\b", query_lower):
            return "price_desc"
        return None

    def _parse_intent(
        self,
        query_lower: str,
        min_price: int | None,
        max_price: int | None,
        exact_model: str | None,
        sort: str | None,
    ) -> str:
        if re.search(r"\b(compare|vs|versus|difference|better)\b", query_lower):
            return "comparison"
        if exact_model:
            return "exact_model"
        if sort:
            return "sort"
        if min_price is not None or max_price is not None:
            return "price_filter"
        if re.search(r"\b(recommend|suggest|best|good)\b", query_lower):
            return "recommendation"
        return "search"

    def _is_followup(self, query_lower: str, filters: QueryFilters, sort: str | None) -> bool:
        words = query_lower.split()
        if sort and len(words) <= 5:
            return True
        if re.search(r"\b(this|that|these|those|one|ones|same|only|just)\b", query_lower):
            return True
        explicit_filter_count = sum(
            value is not None
            for value in [filters.min_price, filters.max_price, filters.brand, filters.color]
        )
        return len(words) <= 4 and explicit_filter_count > 0 and filters.category is None and filters.model is None
