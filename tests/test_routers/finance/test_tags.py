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


async def _create_category(client: AsyncClient, name: str, family_id: str) -> dict:
    res = await client.post("/finance/categories/", json={
        "name": name,
        "family_id": family_id,
    })
    assert res.status_code == 201
    return res.json()


async def _create_tag(client: AsyncClient, name: str, category_id: str, income_type: str = None) -> dict:
    res = await client.post("/finance/tags/", json={
        "name": name,
        "category_id": category_id,
        "income_type": income_type,
    })
    assert res.status_code == 201
    return res.json()


# ── CRUD ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient):
    family = await _create_family(client, "Alimentação")
    cat = await _create_category(client, "Restaurante", family["id"])
    tag = await _create_tag(client, "Restaurante", cat["id"])
    
    assert tag["name"] == "Restaurante"
    assert tag["income_type"] is None
    assert tag["is_active"] is True


@pytest.mark.asyncio
async def test_create_tag_with_income_type(client: AsyncClient):
    family = await _create_family(client, "Renda", nature="income")
    cat = await _create_category(client, "Salário", family["id"])
    tag = await _create_tag(client, "Salário", cat["id"], income_type="active")
    
    assert tag["name"] == "Salário"
    assert tag["income_type"] == "active"


@pytest.mark.asyncio
async def test_create_tag_income_without_income_type(client: AsyncClient):
    family = await _create_family(client, "Renda", nature="income")
    cat = await _create_category(client, "Aluguel", family["id"])
    tag = await _create_tag(client, "Aluguel Recebido", cat["id"])
    
    assert tag["income_type"] is None


@pytest.mark.asyncio
async def test_duplicate_name_returns_409(client: AsyncClient):
    family = await _create_family(client, "Teste")
    cat = await _create_category(client, "Cat1", family["id"])
    await _create_tag(client, "Duplicado", cat["id"])
    
    res = await client.post("/finance/tags/", json={"name": "Duplicado", "category_id": cat["id"]})
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_list_all(client: AsyncClient):
    family = await _create_family(client, "ListTest")
    cat = await _create_category(client, "Cat", family["id"])
    await _create_tag(client, "Tag1", cat["id"])
    await _create_tag(client, "Tag2", cat["id"])
    
    res = await client.get("/finance/tags/")
    assert res.status_code == 200
    assert len(res.json()) >= 2


@pytest.mark.asyncio
async def test_list_filter_by_category(client: AsyncClient):
    family = await _create_family(client, "FilterTest")
    cat1 = await _create_category(client, "Cat1", family["id"])
    cat2 = await _create_category(client, "Cat2", family["id"])
    await _create_tag(client, "Tag1", cat1["id"])
    await _create_tag(client, "Tag2", cat2["id"])
    
    res = await client.get(f"/finance/tags/?category_id={cat1['id']}")
    assert res.status_code == 200
    items = res.json()
    assert all(t["category_id"] == cat1["id"] for t in items)


@pytest.mark.asyncio
async def test_update_tag(client: AsyncClient):
    family = await _create_family(client, "UpdateTest")
    cat = await _create_category(client, "Cat", family["id"])
    tag = await _create_tag(client, "Original", cat["id"])
    
    res = await client.patch(f"/finance/tags/{tag['id']}", json={"name": "Atualizado"})
    assert res.status_code == 200
    assert res.json()["name"] == "Atualizado"


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient):
    family = await _create_family(client, "DeleteTest")
    cat = await _create_category(client, "Cat", family["id"])
    tag = await _create_tag(client, "Para删除", cat["id"])
    
    res = await client.delete(f"/finance/tags/{tag['id']}")
    assert res.status_code == 204
    
    res = await client.get(f"/finance/tags/{tag['id']}")
    assert res.status_code == 404