import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_family(client: AsyncClient, name: str, nature: str = None) -> dict:
    res = await client.post("/finance/tag-families/", json={
        "name": name,
        "nature": nature,
    })
    assert res.status_code == 201
    return res.json()


# ── CRUD ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_family(client: AsyncClient):
    family = await _create_family(client, "Alimentação")
    assert family["name"] == "Alimentação"
    assert family["nature"] is None
    assert family["is_active"] is True


@pytest.mark.asyncio
async def test_create_family_with_nature(client: AsyncClient):
    family = await _create_family(client, "Moradia", nature="fixed_expense")
    assert family["name"] == "Moradia"
    assert family["nature"] == "fixed_expense"


@pytest.mark.asyncio
async def test_create_income_family(client: AsyncClient):
    family = await _create_family(client, "Salário", nature="income")
    assert family["nature"] == "income"


@pytest.mark.asyncio
async def test_create_investment_family(client: AsyncClient):
    family = await _create_family(client, "Ações", nature="investment")
    assert family["nature"] == "investment"


@pytest.mark.asyncio
async def test_duplicate_name_returns_409(client: AsyncClient):
    await _create_family(client, "Duplicado")
    res = await client.post("/finance/tag-families/", json={"name": "Duplicado"})
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_list_all(client: AsyncClient):
    await _create_family(client, "Fam1")
    await _create_family(client, "Fam2")
    
    res = await client.get("/finance/tag-families/")
    assert res.status_code == 200
    assert len(res.json()) >= 2


@pytest.mark.asyncio
async def test_list_filter_by_nature(client: AsyncClient):
    await _create_family(client, "Fixa", nature="fixed_expense")
    await _create_family(client, "Variável", nature="variable_expense")
    await _create_family(client, "Renda", nature="income")
    
    res = await client.get("/finance/tag-families/?nature=income")
    assert res.status_code == 200
    items = res.json()
    assert all(f["nature"] == "income" for f in items)


@pytest.mark.asyncio
async def test_update_family(client: AsyncClient):
    family = await _create_family(client, "Original")
    
    res = await client.patch(f"/finance/tag-families/{family['id']}", json={"name": "Atualizado"})
    assert res.status_code == 200
    assert res.json()["name"] == "Atualizado"


@pytest.mark.asyncio
async def test_update_family_nature(client: AsyncClient):
    family = await _create_family(client, "Despesa")
    
    res = await client.patch(f"/finance/tag-families/{family['id']}", json={"nature": "variable_expense"})
    assert res.status_code == 200
    assert res.json()["nature"] == "variable_expense"


@pytest.mark.asyncio
async def test_delete_family(client: AsyncClient):
    family = await _create_family(client, "Para deletar")
    
    res = await client.delete(f"/finance/tag-families/{family['id']}")
    assert res.status_code == 204
    
    res = await client.get(f"/finance/tag-families/{family['id']}")
    assert res.status_code == 404