# Product Retrieval RAG System

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green)
![React](https://img.shields.io/badge/React-19-61dafb)
![Vite](https://img.shields.io/badge/Vite-7-646cff)
![Pinecone](https://img.shields.io/badge/Pinecone-vector%20search-0b5fff)
![Redis](https://img.shields.io/badge/Redis-session%20memory-dc382d)
![Docker](https://img.shields.io/badge/Docker-ready-2496ed)

Product Retrieval RAG System is a full-stack product search assistant for catalog data. The backend normalizes product CSV data, indexes product metadata, retrieves matching items with exact and vector search, and returns structured RAG answers. The frontend provides a Vite React chat and product-results experience with filters, session-safe state, and product cards.

## Features

- FastAPI backend with `/query`, `/search`, `/clear_memory`, and `/health` endpoints.
- CSV ingestion pipeline with validation, normalization, duplicate detection, and Pinecone document construction.
- Hybrid retrieval using parsed filters, exact matching, optional Pinecone vector search, and structured product responses.
- Redis-backed session memory with an in-memory fallback for local development and tests.
- React + Vite frontend with reusable product cards, filters, product context, and session hooks.
- Evaluation suite for precision, recall, F1, latency, and per-query result tracking.
- Docker Compose stack for API, frontend, and Redis.
- GitHub Actions workflow for backend tests, frontend lint/build/test, and Docker validation.

## Architecture

```text
Product-Retrieval-RAG-System/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── rag/
│   │   ├── memory/
│   │   └── services/
│   ├── tests/
│   ├── eval/
│   └── data/
├── frontend/
│   └── rag-chat-frontend/
├── .github/workflows/
└── docker/
```

The backend loads product data from CSV, normalizes it into `ProductRecord` objects, and supports exact metadata retrieval plus optional Pinecone vector retrieval. The RAG pipeline formats retrieved products into a structured API response and uses session memory so follow-up queries can reuse filters and previous results.

## API Documentation

### `GET /health`

Checks whether the API process is running.

```json
{
  "status": "healthy",
  "message": "Product Retrieval RAG API is running"
}
```

### `POST /query`

Runs a session-aware product RAG query.

Request:

```json
{
  "question": "show Haier microwaves under Rs 50,000",
  "session_id": "demo-session",
  "max_sources": 10
}
```

Response fields:

- `answer`: generated product-search answer.
- `products`: structured product results with price, brand, model, score, and match type.
- `applied_filters`: parsed filters used by the retrieval engine.
- `session_id`: session used for follow-up memory.
- `search_strategy`: exact, vector, hybrid, or fallback strategy label.
- `query_intent`: parsed query intent.
- `latency_ms`: server-side retrieval latency.

### `POST /search`

Runs stateless product retrieval for search-bar interactions.

```json
{
  "query": "iPhone 15 black",
  "max_sources": 8
}
```

### `POST /clear_memory`

Clears stored context for a single session.

```json
{
  "session_id": "demo-session"
}
```

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run backend tests:

```bash
PYTHONPATH=backend pytest
```

Run ingestion:

```bash
PYTHONPATH=backend python -m app.ingestion.pinecone_indexer
```

Run evaluation:

```bash
PYTHONPATH=backend python backend/eval/run_evaluation.py --queries backend/eval/queries.json
```

## Frontend Setup

```bash
cd frontend/rag-chat-frontend
npm install
npm run dev
```

Useful frontend commands:

```bash
npm run lint
npm test
npm run build
```

Set `VITE_API_BASE_URL=http://localhost:8000` for local API calls.

## Docker Setup

```bash
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Redis: `localhost:6379`

## Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `APP_NAME` | No | `Product Retrieval RAG System` | Application display name. |
| `ENVIRONMENT` | No | `development` | Runtime environment label. |
| `LOG_LEVEL` | No | `INFO` | Python logging level. |
| `API_HOST` | No | `0.0.0.0` | Uvicorn host. |
| `API_PORT` | No | `8000` | Uvicorn port. |
| `FRONTEND_URL` | No | `http://localhost:5173` | CORS origin for the frontend. |
| `VITE_API_BASE_URL` | No | `http://localhost:8000` | Frontend API base URL. |
| `PRODUCT_CSV_PATH` | No | `backend/data/products.csv` | Product catalog CSV path. |
| `MAX_SOURCES` | No | `10` | Default maximum retrieved products. |
| `ACTIVE_ONLY_INDEXING` | No | `true` | Exclude inactive products from search/indexing. |
| `REQUIRE_EXTERNAL_SERVICES` | No | `false` | Require Pinecone, Google embeddings, and Redis credentials at startup. |
| `GOOGLE_API_KEY` | External search | empty | Google Generative AI embeddings key. |
| `GROQ_API_KEY` | LLM generation | empty | Optional Groq key for answer generation. |
| `EMBEDDING_MODEL` | No | `models/text-embedding-004` | Embedding model name. |
| `PINECONE_API_KEY` | External search | empty | Pinecone API key. |
| `PINECONE_INDEX_NAME` | External search | `products` | Pinecone index name. |
| `PINECONE_CLOUD` | No | `aws` | Pinecone serverless cloud. |
| `PINECONE_REGION` | No | `us-east-1` | Pinecone serverless region. |
| `REDIS_URL` | Session memory | `redis://localhost:6379/0` | Redis connection URL. |
| `SESSION_TTL_SECONDS` | No | `86400` | Session memory TTL. |

## Tech Stack

- Backend: Python 3.11, FastAPI, Pydantic, LangChain integrations.
- Retrieval: Exact search, query parser, optional Pinecone vector search.
- Memory: Redis session store with deterministic in-memory fallback.
- Frontend: React, Vite, Vitest, Testing Library.
- CI/CD: GitHub Actions, Docker, Docker Compose.

## Repository

GitHub: <https://github.com/husnainhashmi5/Product-Retrieval-RAG-System>
