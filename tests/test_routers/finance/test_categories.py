import pytest
from httpx import AsyncClient


async def _create_family(client: AsyncClient, name: str = "Gastos de Casa") -> str:
    res = await client.post("/finance/tag-families/", json={"name": name})
    return res.json()["id"]


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient):
    """Categoria não tem mais campo type — apenas name e family_id opcional."""
    response = await client.post("/finance/categories/", json={"name": "Alimentação"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alimentação"
    assert data["family_id"] is None
    assert "type" not in data


@pytest.mark.asyncio
async def test_create_category_with_family(client: AsyncClient):
    family_id = await _create_family(client, "Lazer")
    response = await client.post(
        "/finance/categories/",
        json={"name": "Cinema", "family_id": family_id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cinema"
    assert data["family_id"] == family_id


@pytest.mark.asyncio
async def test_update_category_family(client: AsyncClient):
    family_id = await _create_family(client, "Mensalidades")
    create_res = await client.post("/finance/categories/", json={"name": "Streaming"})
    category_id = create_res.json()["id"]
    assert create_res.json()["family_id"] is None

    response = await client.patch(f"/finance/categories/{category_id}", json={"family_id": family_id})
    assert response.status_code == 200
    assert response.json()["family_id"] == family_id


@pytest.mark.asyncio
async def test_category_accepts_tags_of_both_types(client: AsyncClient):
    """Regra 1: mesma categoria pode ter tags outcome e income."""
    cat_res = await client.post("/finance/categories/", json={"name": "Investimentos"})
    cat_id = cat_res.json()["id"]

    r_out = await client.post("/finance/tags/", json={"name": "Aporte", "category_id": cat_id, "type": "outcome"})
    r_in  = await client.post("/finance/tags/", json={"name": "Resgate", "category_id": cat_id, "type": "income"})

    assert r_out.status_code == 201
    assert r_in.status_code == 201
    assert r_out.json()["type"] == "outcome"
    assert r_in.json()["type"] == "income"


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient):
    await client.post("/finance/categories/", json={"name": "Salário"})
    response = await client.get("/finance/categories/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient):
    create_res = await client.post("/finance/categories/", json={"name": "Saúde"})
    category_id = create_res.json()["id"]
    response = await client.patch(f"/finance/categories/{category_id}", json={"name": "Saúde e Bem-estar"})
    assert response.status_code == 200
    assert response.json()["name"] == "Saúde e Bem-estar"


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient):
    create_res = await client.post("/finance/categories/", json={"name": "Temporária"})
    category_id = create_res.json()["id"]
    assert (await client.delete(f"/finance/categories/{category_id}")).status_code == 204


@pytest.mark.asyncio
async def test_get_nonexistent_category(client: AsyncClient):
    response = await client.get("/finance/categories/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
