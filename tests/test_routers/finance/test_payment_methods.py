import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_payment_method(client: AsyncClient, name: str, type: str, account_id: str) -> dict:
    res = await client.post("/finance/payment-methods/", json={
        "name": name,
        "type": type,
        "account_id": account_id,
    })
    assert res.status_code == 201
    return res.json()


# ── CRUD ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_payment_method(client: AsyncClient, test_account: dict):
    pm = await _create_payment_method(client, "Nubank Débito", "debit", test_account["id"])
    assert pm["name"] == "Nubank Débito"
    assert pm["type"] == "debit"
    assert pm["is_active"] is True


@pytest.mark.asyncio
async def test_create_credit_method(client: AsyncClient, test_account: dict):
    pm = await _create_payment_method(client, "Nubank Crédito", "credit", test_account["id"])
    assert pm["type"] == "credit"


@pytest.mark.asyncio
async def test_create_benefit_method(client: AsyncClient, test_account: dict):
    pm = await _create_payment_method(client, "Vale Refeição", "benefit", test_account["id"])
    assert pm["type"] == "benefit"


@pytest.mark.asyncio
async def test_duplicate_name_returns_409(client: AsyncClient, test_account: dict):
    await _create_payment_method(client, "PIX", "debit", test_account["id"])
    res = await client.post("/finance/payment-methods/", json={
        "name": "PIX",
        "type": "debit",
        "account_id": test_account["id"],
    })
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_list_all(client: AsyncClient, test_account: dict):
    await _create_payment_method(client, "Débito", "debit", test_account["id"])
    await _create_payment_method(client, "Crédito", "credit", test_account["id"])
    
    res = await client.get("/finance/payment-methods/")
    assert res.status_code == 200
    assert len(res.json()) >= 2


@pytest.mark.asyncio
async def test_list_filter_active(client: AsyncClient, test_account: dict):
    pm = await _create_payment_method(client, "Ativo", "debit", test_account["id"])
    await client.patch(f"/finance/payment-methods/{pm['id']}", json={"is_active": False})
    
    active = await client.get("/finance/payment-methods/?is_active=true")
    assert active.status_code == 200
    assert all(m["is_active"] for m in active.json())


@pytest.mark.asyncio
async def test_update_payment_method(client: AsyncClient, test_account: dict):
    pm = await _create_payment_method(client, "Original", "debit", test_account["id"])
    
    res = await client.patch(f"/finance/payment-methods/{pm['id']}", json={"name": "Atualizado"})
    assert res.status_code == 200
    assert res.json()["name"] == "Atualizado"


@pytest.mark.asyncio
async def test_delete_payment_method(client: AsyncClient, test_account: dict):
    pm = await _create_payment_method(client, "Para deletar", "debit", test_account["id"])
    
    res = await client.delete(f"/finance/payment-methods/{pm['id']}")
    assert res.status_code == 204
    
    res = await client.get(f"/finance/payment-methods/{pm['id']}")
    assert res.status_code == 404