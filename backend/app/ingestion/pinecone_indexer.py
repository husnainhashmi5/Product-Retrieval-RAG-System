from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.ingestion.csv_loader import IngestionReport, load_products_from_csv
from app.ingestion.normalizer import ProductRecord


def build_embedding_text(product: ProductRecord) -> str:
    return product.searchable_text()


def build_pinecone_documents(products: list[ProductRecord]):
    from langchain_core.documents import Document

    return [
        Document(page_content=build_embedding_text(product), metadata=product.to_metadata())
        for product in products
    ]


def write_validation_report(report: IngestionReport, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total_rows": report.total_rows,
        "indexed_count": report.indexed_count,
        "rejected_count": report.rejected_count,
        "duplicates": report.duplicates,
        "rejected": [
            {
                "product_id": item.product_id,
                "row_number": item.row_number,
                "reasons": item.reasons,
            }
            for item in report.rejected
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def ingest_products(settings: Settings | None = None) -> IngestionReport:
    settings = settings or Settings.from_env()
    settings.validate()

    report = load_products_from_csv(
        settings.resolved_csv_path(),
        active_only=settings.active_only_indexing,
    )
    documents = build_pinecone_documents(report.products)

    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_pinecone import PineconeVectorStore

    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
        task_type="RETRIEVAL_DOCUMENT",
    )
    PineconeVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        index_name=settings.pinecone_index_name,
    )
    return report


def main() -> None:
    settings = Settings.from_env()
    report = ingest_products(settings)
    report_path = Path("reports") / "ingestion_report.json"
    write_validation_report(report, report_path)
    print(
        f"Indexed {report.indexed_count} active products from {report.total_rows} rows. "
        f"Rejected {report.rejected_count}. Report: {report_path}"
    )


if __name__ == "__main__":
    main()
