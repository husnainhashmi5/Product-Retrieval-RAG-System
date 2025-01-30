from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from app.ingestion.normalizer import ProductRecord, ValidationReport, normalize_product_row, validate_product


@dataclass(frozen=True)
class IngestionReport:
    products: list[ProductRecord]
    rejected: list[ValidationReport]
    duplicates: dict[str, list[int]] = field(default_factory=dict)
    total_rows: int = 0

    @property
    def indexed_count(self) -> int:
        return len(self.products)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)


def load_products_from_csv(path: str | Path, *, active_only: bool = True) -> IngestionReport:
    csv_path = Path(path)
    products: list[ProductRecord] = []
    rejected: list[ValidationReport] = []
    seen_rows: dict[str, list[int]] = {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        total_rows = 0
        for row_number, row in enumerate(reader, start=2):
            total_rows += 1
            product = normalize_product_row(row, row_number=row_number)
            report = validate_product(product, active_only=active_only, row_number=row_number)
            seen_rows.setdefault(product.product_id, []).append(row_number)
            if report.is_valid:
                products.append(product)
            else:
                rejected.append(report)

    duplicates = {product_id: rows for product_id, rows in seen_rows.items() if len(rows) > 1}
    return IngestionReport(
        products=products,
        rejected=rejected,
        duplicates=duplicates,
        total_rows=total_rows,
    )
