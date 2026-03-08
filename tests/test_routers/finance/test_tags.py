import pytest
from httpx import AsyncClient


async def _create_category(client: AsyncClient, name: str = "Food") -> str:
    res = await client.post("/finance/categories/", json={"name": name, "type": "outcome"})
    return res.json()["id"]


@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient):
    cat_id = await _create_category(client)
    response = await client.post("/finance/tags/", json={"name": "Restaurant", "category_id": cat_id})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Restaurant"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_tags_by_category(client: AsyncClient):
    cat_id = await _create_category(client, "Transport")
    await client.post("/finance/tags/", json={"name": "Uber", "category_id": cat_id})
    response = await client.get(f"/finance/tags/?category_id={cat_id}")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_deactivate_tag(client: AsyncClient):
    cat_id = await _create_category(client, "Misc")
    create = await client.post("/finance/tags/", json={"name": "OldTag", "category_id": cat_id})
    tag_id = create.json()["id"]
    response = await client.patch(f"/finance/tags/{tag_id}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient):
    cat_id = await _create_category(client, "Temp")
    create = await client.post("/finance/tags/", json={"name": "TempTag", "category_id": cat_id})
    tag_id = create.json()["id"]
    assert (await client.delete(f"/finance/tags/{tag_id}")).status_code == 204
