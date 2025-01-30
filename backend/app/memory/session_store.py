from __future__ import annotations

import threading
from dataclasses import dataclass, field

from app.retrieval.query_parser import QueryFilters


@dataclass
class SessionContext:
    current_category: str | None = None
    current_min_price: int | None = None
    current_max_price: int | None = None
    current_brand: str | None = None
    current_color: str | None = None
    previous_result_ids: list[str] = field(default_factory=list)
    previous_sort: str | None = None
    previous_comparison: str | None = None

    def to_filters(self) -> QueryFilters:
        return QueryFilters(
            min_price=self.current_min_price,
            max_price=self.current_max_price,
            category=self.current_category,
            brand=self.current_brand,
            color=self.current_color,
            status="active",
        )

    def update(self, filters: QueryFilters, result_ids: list[str], sort: str | None = None) -> None:
        self.current_category = filters.category
        self.current_min_price = filters.min_price
        self.current_max_price = filters.max_price
        self.current_brand = filters.brand
        self.current_color = filters.color
        self.previous_result_ids = result_ids
        self.previous_sort = sort


class SessionStore:
    def __init__(self) -> None:
        self._contexts: dict[str, SessionContext] = {}
        self._lock = threading.Lock()

    def get_context(self, session_id: str | None) -> SessionContext:
        key = session_id or "default_session"
        with self._lock:
            if key not in self._contexts:
                self._contexts[key] = SessionContext()
            return self._contexts[key]

    def clear_session(self, session_id: str) -> None:
        if not session_id:
            raise ValueError("session_id is required")
        with self._lock:
            self._contexts.pop(session_id, None)

    def has_session(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._contexts
