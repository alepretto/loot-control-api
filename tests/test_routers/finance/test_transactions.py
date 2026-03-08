from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

NOW = datetime.now(timezone.utc).isoformat()


async def _setup(client: AsyncClient) -> str:
    """Cria categoria + tag income e retorna o tag_id."""
    cat = await client.post("/finance/categories/", json={"name": "Receitas"})
    tag = await client.post(
        "/finance/tags/",
        json={"name": "Salário", "category_id": cat.json()["id"], "type": "income"},
    )
    return tag.json()["id"]


async def _setup_outcome(client: AsyncClient) -> str:
    """Cria categoria + tag outcome e retorna o tag_id."""
    cat = await client.post("/finance/categories/", json={"name": "Despesas"})
    tag = await client.post(
        "/finance/tags/",
        json={"name": "Mercado", "category_id": cat.json()["id"], "type": "outcome"},
    )
    return tag.json()["id"]


@pytest.mark.asyncio
async def test_create_transaction(client: AsyncClient):
    tag_id = await _setup(client)
    response = await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_id, "date_transaction": NOW, "value": 5000.0, "currency": "BRL"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == 5000.0
    assert data["currency"] == "BRL"


@pytest.mark.asyncio
async def test_transaction_type_from_tag(client: AsyncClient):
    """O tipo da transação é determinado pela tag, não pela categoria."""
    cat_id = (await client.post("/finance/categories/", json={"name": "Investimentos"})).json()["id"]
    tag_in  = (await client.post("/finance/tags/", json={"name": "Resgate", "category_id": cat_id, "type": "income"})).json()
    tag_out = (await client.post("/finance/tags/", json={"name": "Aporte",  "category_id": cat_id, "type": "outcome"})).json()

    r_in  = await client.post("/finance/transactions/", json={"tag_id": tag_in["id"],  "date_transaction": NOW, "value": 1000.0, "currency": "BRL"})
    r_out = await client.post("/finance/transactions/", json={"tag_id": tag_out["id"], "date_transaction": NOW, "value": 500.0,  "currency": "BRL"})

    assert r_in.status_code == 201
    assert r_out.status_code == 201
    # O tipo é inferido da tag, não da transação em si
    assert r_in.json()["tag_id"] == tag_in["id"]
    assert r_out.json()["tag_id"] == tag_out["id"]


@pytest.mark.asyncio
async def test_create_investment_transaction(client: AsyncClient):
    tag_id = await _setup_outcome(client)
    response = await client.post(
        "/finance/transactions/",
        json={
            "tag_id": tag_id,
            "date_transaction": NOW,
            "value": 1000.0,
            "currency": "USD",
            "quantity": 0.01,
            "symbol": "BTC",
            "index_rate": 95000.0,
            "index": "CoinGecko",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "BTC"
    assert data["quantity"] == 0.01


@pytest.mark.asyncio
async def test_list_transactions_paginated(client: AsyncClient):
    tag_id = await _setup(client)
    for i in range(5):
        await client.post(
            "/finance/transactions/",
            json={"tag_id": tag_id, "date_transaction": NOW, "value": float(i * 100 + 1), "currency": "BRL"},
        )
    response = await client.get("/finance/transactions/?page=1&page_size=3")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data and "total" in data
    assert len(data["items"]) <= 3


@pytest.mark.asyncio
async def test_update_transaction(client: AsyncClient):
    tag_id = await _setup(client)
    create = await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_id, "date_transaction": NOW, "value": 200.0, "currency": "BRL"},
    )
    tx_id = create.json()["id"]
    response = await client.patch(f"/finance/transactions/{tx_id}", json={"value": 250.0})
    assert response.status_code == 200
    assert response.json()["value"] == 250.0


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient):
    tag_id = await _setup(client)
    create = await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_id, "date_transaction": NOW, "value": 100.0, "currency": "BRL"},
    )
    tx_id = create.json()["id"]
    assert (await client.delete(f"/finance/transactions/{tx_id}")).status_code == 204


@pytest.mark.asyncio
async def test_get_nonexistent_transaction(client: AsyncClient):
    response = await client.get("/finance/transactions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
