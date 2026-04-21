import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_family(client: AsyncClient, name: str, nature: str = None) -> dict:
    res = await client.post("/finance/tag-families/", json={"name": name, "nature": nature})
    assert res.status_code == 201
    return res.json()


async def _create_category(client: AsyncClient, name: str, family_id: str) -> dict:
    res = await client.post("/finance/categories/", json={"name": name, "family_id": family_id})
    assert res.status_code == 201
    return res.json()


async def _create_tag(client: AsyncClient, name: str, category_id: str) -> dict:
    res = await client.post("/finance/tags/", json={"name": name, "category_id": category_id})
    assert res.status_code == 201
    return res.json()


# ── CRUD ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_transaction(client: AsyncClient, test_account: dict):
    family = await _create_family(client, "Despesa", nature="variable_expense")
    cat = await _create_category(client, "Alimentação", family["id"])
    tag = await _create_tag(client, "Supermercado", cat["id"])
    
    res = await client.post("/finance/transactions/", json={
        "tag_id": tag["id"],
        "account_id": test_account["id"],
        "date_transaction": "2026-04-19T12:00:00Z",
        "value": 150.00,
        "currency": "BRL",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["value"] == 150.00
    assert data["account_id"] == test_account["id"]


@pytest.mark.asyncio
async def test_create_transaction_with_investment(client: AsyncClient, test_account: dict):
    family = await _create_family(client, "Investimento", nature="investment")
    cat = await _create_category(client, "Ações", family["id"])
    tag = await _create_tag(client, "PETR4", cat["id"])
    
    res = await client.post("/finance/transactions/", json={
        "tag_id": tag["id"],
        "account_id": test_account["id"],
        "date_transaction": "2026-04-19T12:00:00Z",
        "value": 10000.00,
        "currency": "BRL",
        "quantity": 100,
        "symbol": "PETR4",
        "index": "IBOV",
        "index_rate": 1.0,
    })
    assert res.status_code == 201
    data = res.json()
    assert data["symbol"] == "PETR4"
    assert data["quantity"] == 100


@pytest.mark.asyncio
async def test_list_transactions(client: AsyncClient, test_account: dict):
    family = await _create_family(client, "ListTest")
    cat = await _create_category(client, "Cat", family["id"])
    tag = await _create_tag(client, "Tag", cat["id"])
    
    await client.post("/finance/transactions/", json={
        "tag_id": tag["id"],
        "account_id": test_account["id"],
        "date_transaction": "2026-04-19T12:00:00Z",
        "value": 50.00,
        "currency": "BRL",
    })
    
    res = await client.get("/finance/transactions/")
    assert res.status_code == 200
    assert res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_filter_by_account_id(client: AsyncClient, test_account: dict, test_account_credit: dict):
    family = await _create_family(client, "Filtro")
    cat = await _create_category(client, "Cat", family["id"])
    tag = await _create_tag(client, "Tag", cat["id"])
    
    await client.post("/finance/transactions/", json={
        "tag_id": tag["id"],
        "account_id": test_account["id"],
        "date_transaction": "2026-04-19T12:00:00Z",
        "value": 100.00,
        "currency": "BRL",
    })
    
    res = await client.get(f"/finance/transactions/?account_id={test_account['id']}")
    assert res.status_code == 200
    items = res.json()["items"]
    assert all(t["account_id"] == test_account["id"] for t in items)


@pytest.mark.asyncio
async def test_filter_by_nature(client: AsyncClient, test_account: dict):
    family_fixed = await _create_family(client, "Fixo", nature="fixed_expense")
    cat_fixed = await _create_category(client, "Aluguel", family_fixed["id"])
    tag_fixed = await _create_tag(client, "Aluguel", cat_fixed["id"])
    
    family_variable = await _create_family(client, "Variavel", nature="variable_expense")
    cat_var = await _create_category(client, "Mercado", family_variable["id"])
    tag_var = await _create_tag(client, "Mercado", cat_var["id"])
    
    await client.post("/finance/transactions/", json={
        "tag_id": tag_fixed["id"],
        "account_id": test_account["id"],
        "date_transaction": "2026-04-19T12:00:00Z",
        "value": 1500.00,
        "currency": "BRL",
    })
    
    res = await client.get("/finance/transactions/?nature=fixed_expense")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_update_transaction(client:AsyncClient, test_account: dict):
    family = await _create_family(client, "Update")
    cat = await _create_category(client, "Cat", family["id"])
    tag = await _create_tag(client, "Tag", cat["id"])
    
    tx = await client.post("/finance/transactions/", json={
        "tag_id": tag["id"],
        "account_id": test_account["id"],
        "date_transaction": "2026-04-19T12:00:00Z",
        "value": 100.00,
        "currency": "BRL",
    })
    tx_id = tx.json()["id"]
    
    res = await client.patch(f"/finance/transactions/{tx_id}", json={"value": 200.00})
    assert res.status_code == 200
    assert res.json()["value"] == 200.00


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient, test_account: dict):
    family = await _create_family(client, "Delete")
    cat = await _create_category(client, "Cat", family["id"])
    tag = await _create_tag(client, "Tag", cat["id"])
    
    tx = await client.post("/finance/transactions/", json={
        "tag_id": tag["id"],
        "account_id": test_account["id"],
        "date_transaction": "2026-04-19T12:00:00Z",
        "value": 50.00,
        "currency": "BRL",
    })
    tx_id = tx.json()["id"]
    
    res = await client.delete(f"/finance/transactions/{tx_id}")
    assert res.status_code == 204