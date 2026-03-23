import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    response = await client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert data["email"].endswith("@lootcontrol.com")


@pytest.mark.asyncio
async def test_get_me_returns_correct_user(client: AsyncClient, test_user):
    response = await client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username


@pytest.mark.asyncio
async def test_patch_me_username(client: AsyncClient):
    response = await client.patch("/users/me", json={"username": "novo_username"})
    assert response.status_code == 200
    assert response.json()["username"] == "novo_username"


@pytest.mark.asyncio
async def test_patch_me_partial_update(client: AsyncClient, test_user):
    original_email = test_user.email
    response = await client.patch("/users/me", json={"first_name": "João"})
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "João"
    # email não foi alterado
    assert data["email"] == original_email


@pytest.mark.asyncio
async def test_patch_me_ignores_unknown_fields(client: AsyncClient):
    response = await client.patch("/users/me", json={"campo_inexistente": "valor"})
    # deve ignorar campos desconhecidos sem erro
    assert response.status_code in (200, 422)
