import pytest
from httpx import AsyncClient

from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).isoformat()


async def _create_family(client: AsyncClient, name: str = "Gastos de Casa") -> str:
    res = await client.post("/finance/tag-families/", json={"name": name})
    assert res.status_code == 201
    return res.json()["id"]


async def _create_cat(client: AsyncClient, name: str, family_id: str | None = None) -> str:
    payload: dict = {"name": name}
    if family_id:
        payload["family_id"] = family_id
    res = await client.post("/finance/categories/", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


async def _create_tag(client: AsyncClient, name: str, cat_id: str, type_: str = "outcome") -> str:
    res = await client.post("/finance/tags/", json={"name": name, "category_id": cat_id, "type": type_})
    assert res.status_code == 201
    return res.json()["id"]


async def _create_tx(client: AsyncClient, tag_id: str) -> str:
    res = await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_id, "date_transaction": NOW, "value": 100.0, "currency": "BRL"},
    )
    assert res.status_code == 201
    return res.json()["id"]


@pytest.mark.asyncio
async def test_create_tag_family(client: AsyncClient):
    response = await client.post("/finance/tag-families/", json={"name": "Lazer"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Lazer"
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_create_duplicate_family_returns_409(client: AsyncClient):
    """Não permite criar duas famílias com o mesmo nome."""
    await client.post("/finance/tag-families/", json={"name": "DupFam"})
    response = await client.post("/finance/tag-families/", json={"name": "DupFam"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_tag_families(client: AsyncClient):
    await _create_family(client, "Mensalidades")
    await _create_family(client, "Transporte")
    response = await client.get("/finance/tag-families/")
    assert response.status_code == 200
    names = [f["name"] for f in response.json()]
    assert "Mensalidades" in names
    assert "Transporte" in names


@pytest.mark.asyncio
async def test_get_tag_family(client: AsyncClient):
    family_id = await _create_family(client, "Investimentos")
    response = await client.get(f"/finance/tag-families/{family_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Investimentos"


@pytest.mark.asyncio
async def test_get_nonexistent_tag_family(client: AsyncClient):
    response = await client.get("/finance/tag-families/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_tag_family(client: AsyncClient):
    family_id = await _create_family(client, "Antigo Nome")
    response = await client.patch(f"/finance/tag-families/{family_id}", json={"name": "Novo Nome"})
    assert response.status_code == 200
    assert response.json()["name"] == "Novo Nome"


@pytest.mark.asyncio
async def test_delete_tag_family(client: AsyncClient):
    family_id = await _create_family(client, "Temporária")
    assert (await client.delete(f"/finance/tag-families/{family_id}")).status_code == 204
    assert (await client.get(f"/finance/tag-families/{family_id}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_family_cascades_categories_tags_transactions(client: AsyncClient):
    """Excluir família → apaga cascata: categorias → tags → transações."""
    family_id = await _create_family(client, "Família Cascata")
    cat_id = await _create_cat(client, "Cat Cascata", family_id)
    tag_id = await _create_tag(client, "Tag Cascata", cat_id)
    tx_id = await _create_tx(client, tag_id)

    await client.delete(f"/finance/tag-families/{family_id}")

    assert (await client.get(f"/finance/categories/{cat_id}")).status_code == 404
    assert (await client.get(f"/finance/tags/{tag_id}")).status_code == 404
    assert (await client.get(f"/finance/transactions/{tx_id}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_category_cascades_tags_transactions(client: AsyncClient):
    """Excluir categoria → apaga cascata: tags → transações."""
    cat_id = await _create_cat(client, "Cat Para Deletar")
    tag_id = await _create_tag(client, "Tag Para Deletar", cat_id)
    tx_id = await _create_tx(client, tag_id)

    assert (await client.delete(f"/finance/categories/{cat_id}")).status_code == 204

    assert (await client.get(f"/finance/tags/{tag_id}")).status_code == 404
    assert (await client.get(f"/finance/transactions/{tx_id}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_tag_cascades_transactions(client: AsyncClient):
    """Excluir tag → apaga cascata: transações."""
    cat_id = await _create_cat(client, "Cat Tx Cascata")
    tag_id = await _create_tag(client, "Tag Tx Cascata", cat_id)
    tx_id = await _create_tx(client, tag_id)

    assert (await client.delete(f"/finance/tags/{tag_id}")).status_code == 204
    assert (await client.get(f"/finance/transactions/{tx_id}")).status_code == 404


@pytest.mark.asyncio
async def test_update_family_name(client: AsyncClient):
    """PATCH no nome da família: novo nome retornado e persistido."""
    family_id = await _create_family(client, "FamNomeAntigo")

    response = await client.patch(f"/finance/tag-families/{family_id}", json={"name": "FamNomeNovo"})
    assert response.status_code == 200
    assert response.json()["name"] == "FamNomeNovo"

    # Verificar persistência via GET
    get_res = await client.get(f"/finance/tag-families/{family_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "FamNomeNovo"


@pytest.mark.asyncio
async def test_list_families_returns_all(client: AsyncClient):
    """Cria 2 famílias, verifica que ambas aparecem na listagem."""
    names = ["FamListA", "FamListB"]
    for name in names:
        await _create_family(client, name)

    response = await client.get("/finance/tag-families/")
    assert response.status_code == 200
    returned_names = [f["name"] for f in response.json()]
    for name in names:
        assert name in returned_names
