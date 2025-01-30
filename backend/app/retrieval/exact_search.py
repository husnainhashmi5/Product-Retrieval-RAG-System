from __future__ import annotations

import re

from app.ingestion.normalizer import ProductRecord, normalize_model


def compact_model(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", normalize_model(value))


def find_exact_model_matches(products: list[ProductRecord], model: str | None) -> list[ProductRecord]:
    if not model:
        return []

    wanted = compact_model(model)
    if not wanted:
        return []

    exact: list[ProductRecord] = []
    partial: list[ProductRecord] = []
    for product in products:
        product_model = compact_model(product.model)
        if product_model == wanted:
            exact.append(product)
        elif wanted and wanted in product_model:
            partial.append(product)
    return exact or partial
