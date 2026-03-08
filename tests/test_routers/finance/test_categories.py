import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient):
    response = await client.post("/finance/categories/", json={"name": "Food", "type": "outcome"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Food"
    assert data["type"] == "outcome"


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient):
    await client.post("/finance/categories/", json={"name": "Salary", "type": "income"})
    response = await client.get("/finance/categories/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_categories_filter_by_type(client: AsyncClient):
    await client.post("/finance/categories/", json={"name": "Transport", "type": "outcome"})
    response = await client.get("/finance/categories/?type=outcome")
    assert response.status_code == 200
    for item in response.json():
        assert item["type"] == "outcome"


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient):
    create_res = await client.post("/finance/categories/", json={"name": "Health", "type": "outcome"})
    category_id = create_res.json()["id"]
    response = await client.patch(f"/finance/categories/{category_id}", json={"name": "Healthcare"})
    assert response.status_code == 200
    assert response.json()["name"] == "Healthcare"


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient):
    create_res = await client.post("/finance/categories/", json={"name": "ToDelete", "type": "outcome"})
    category_id = create_res.json()["id"]
    assert (await client.delete(f"/finance/categories/{category_id}")).status_code == 204


@pytest.mark.asyncio
async def test_get_nonexistent_category(client: AsyncClient):
    response = await client.get("/finance/categories/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
