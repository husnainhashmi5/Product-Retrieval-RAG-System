from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _as_bool(value: str | bool | None, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value: str | int | None, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


@dataclass(slots=True)
class Settings:
    app_name: str = "Product Retrieval RAG System"
    environment: str = "development"
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:5173"
    product_csv_path: str = "backend/data/products.csv"
    max_sources: int = 10
    active_only_indexing: bool = True
    require_external_services: bool = False
    google_api_key: str = ""
    groq_api_key: str = ""
    embedding_model: str = "models/text-embedding-004"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "products-rag"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 86400

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            environment=os.getenv("ENVIRONMENT", cls.environment),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
            frontend_url=os.getenv("FRONTEND_URL", cls.frontend_url),
            product_csv_path=os.getenv("PRODUCT_CSV_PATH", cls.product_csv_path),
            max_sources=_as_int(os.getenv("MAX_SOURCES"), cls.max_sources),
            active_only_indexing=_as_bool(os.getenv("ACTIVE_ONLY_INDEXING"), cls.active_only_indexing),
            require_external_services=_as_bool(os.getenv("REQUIRE_EXTERNAL_SERVICES"), cls.require_external_services),
            google_api_key=os.getenv("GOOGLE_API_KEY", cls.google_api_key),
            groq_api_key=os.getenv("GROQ_API_KEY", cls.groq_api_key),
            embedding_model=os.getenv("EMBEDDING_MODEL", cls.embedding_model),
            pinecone_api_key=os.getenv("PINECONE_API_KEY", cls.pinecone_api_key),
            pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", cls.pinecone_index_name),
            pinecone_cloud=os.getenv("PINECONE_CLOUD", cls.pinecone_cloud),
            pinecone_region=os.getenv("PINECONE_REGION", cls.pinecone_region),
            redis_url=os.getenv("REDIS_URL", cls.redis_url),
            session_ttl_seconds=_as_int(os.getenv("SESSION_TTL_SECONDS"), cls.session_ttl_seconds),
        )

    def resolved_csv_path(self) -> Path:
        path = Path(self.product_csv_path)
        if path.is_absolute():
            return path
        return Path.cwd() / path

    def validate(self) -> None:
        missing = []
        if self.require_external_services:
            required_values = {
                "GOOGLE_API_KEY": self.google_api_key,
                "PINECONE_API_KEY": self.pinecone_api_key,
                "PINECONE_INDEX_NAME": self.pinecone_index_name,
            }
            missing = [name for name, value in required_values.items() if not value]

        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {joined}")

        if self.max_sources <= 0:
            raise ValueError("MAX_SOURCES must be greater than 0")

        if self.session_ttl_seconds <= 0:
            raise ValueError("SESSION_TTL_SECONDS must be greater than 0")
