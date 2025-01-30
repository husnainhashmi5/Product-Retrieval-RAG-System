import asyncio

import httpx

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


def make_app():
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
    return create_app(settings=settings, rag_system=rag)


async def post_json(app, path, payload):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=payload)


def run(coro):
    return asyncio.run(coro)


def test_query_returns_structured_products_and_filters():
    app = make_app()

    response = run(post_json(
        app,
        "/query",
        {"question": "show microwaves under Rs 50,000", "session_id": "s1"},
    ))

    assert response.status_code == 200
    payload = response.json()
    assert payload["products"][0]["product_id"] == "p1"
    assert payload["products"][0]["price"] == 49000
    assert payload["applied_filters"]["max_price"] == 50000
    assert payload["applied_filters"]["status"] == "active"


def test_search_route_uses_existing_product_search_method():
    app = make_app()

    response = run(post_json(app, "/search", {"query": "HMW-20"}))

    assert response.status_code == 200
    assert response.json()["products"][0]["model"] == "HMW-20"


async def clear_memory_scenario():
    app = make_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/query", json={"question": "show microwaves", "session_id": "a"})
        await client.post("/query", json={"question": "show microwaves", "session_id": "b"})
        response = await client.post("/clear_memory", json={"session_id": "a"})

    store = app.state.rag.session_store
    return (
        response,
        store.get_context("a").previous_result_ids,
        store.get_context("b").previous_result_ids,
    )


def test_clear_memory_requires_body_session_id_and_clears_only_that_session():
    response, first_session_results, second_session_results = run(clear_memory_scenario())

    assert response.status_code == 200
    assert first_session_results == []
    assert second_session_results == ["p1", "p3"]


def test_clear_memory_rejects_missing_session_id():
    app = make_app()

    response = run(post_json(app, "/clear_memory", {}))

    assert response.status_code == 422


async def empty_result_scenario():
    app = make_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        empty = await client.post("/query", json={"question": "Samsung phones under Rs 100", "session_id": "s1"})
        invalid = await client.post("/query", json={"question": "", "session_id": "s1"})
    return empty, invalid


def test_empty_result_and_invalid_request_handling():
    empty, invalid = run(empty_result_scenario())

    assert empty.status_code == 200
    assert empty.json()["products"] == []
    assert empty.json()["answer"].lower().startswith("i couldn't find")
    assert invalid.status_code == 422
