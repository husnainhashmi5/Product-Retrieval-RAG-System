from fastapi.testclient import TestClient

from app.core.config import Settings
from app.ingestion.normalizer import ProductRecord
from app.main import create_app
from app.rag.pipeline import RAGSystem


def make_product(product_id, name, brand, model, price, category, color, status="active"):
    return ProductRecord(
        product_id=product_id,
        name=name,
        brand=brand,
        model=model,
        category=category,
        price=price,
        color=color,
        variation=color,
        status=status,
        source_url="",
        source_row=product_id,
        raw={},
    )


def make_client():
    settings = Settings(
        groq_api_key="test",
        pinecone_api_key="test",
        pinecone_index_name="test-index",
        frontend_url="http://localhost:5173",
        require_external_services=False,
    )
    rag = RAGSystem(
        settings=settings,
        products=[
            make_product("p1", "Budget Microwave", "Haier", "HMW-20", 49000, "microwave", "Black"),
            make_product("p2", "Inactive Microwave", "Haier", "HMW-OLD", 10000, "microwave", "Black", "inactive"),
            make_product("p3", "Premium Microwave", "Haier", "HMW-99", 90000, "microwave", "Black"),
        ],
    )
    return TestClient(create_app(settings=settings, rag_system=rag))


def test_query_returns_structured_products_and_filters():
    client = make_client()

    response = client.post(
        "/query",
        json={"question": "show microwaves under Rs 50,000", "session_id": "s1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["products"][0]["product_id"] == "p1"
    assert payload["products"][0]["price"] == 49000
    assert payload["applied_filters"]["max_price"] == 50000
    assert payload["applied_filters"]["status"] == "active"


def test_search_route_uses_existing_product_search_method():
    client = make_client()

    response = client.post("/search", json={"query": "HMW-20"})

    assert response.status_code == 200
    assert response.json()["products"][0]["model"] == "HMW-20"


def test_clear_memory_requires_body_session_id_and_clears_only_that_session():
    client = make_client()
    client.post("/query", json={"question": "show microwaves", "session_id": "a"})
    client.post("/query", json={"question": "show microwaves", "session_id": "b"})

    response = client.post("/clear_memory", json={"session_id": "a"})

    assert response.status_code == 200
    store = client.app.state.rag.session_store
    assert store.get_context("a").previous_result_ids == []
    assert store.get_context("b").previous_result_ids == ["p1", "p3"]


def test_clear_memory_rejects_missing_session_id():
    client = make_client()

    response = client.post("/clear_memory", json={})

    assert response.status_code == 422


def test_empty_result_and_invalid_request_handling():
    client = make_client()

    empty = client.post("/query", json={"question": "Samsung phones under Rs 100", "session_id": "s1"})
    invalid = client.post("/query", json={"question": "", "session_id": "s1"})

    assert empty.status_code == 200
    assert empty.json()["products"] == []
    assert empty.json()["answer"].lower().startswith("i couldn't find")
    assert invalid.status_code == 422
