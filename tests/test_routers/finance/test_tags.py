import pytest
from httpx import AsyncClient


async def _create_category(client: AsyncClient, name: str = "Alimentação") -> str:
    res = await client.post("/finance/categories/", json={"name": name})
    return res.json()["id"]


@pytest.mark.asyncio
async def test_create_tag_outcome(client: AsyncClient):
    cat_id = await _create_category(client)
    response = await client.post(
        "/finance/tags/", json={"name": "Restaurante", "category_id": cat_id, "type": "outcome"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Restaurante"
    assert data["type"] == "outcome"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_tag_income(client: AsyncClient):
    cat_id = await _create_category(client, "Receitas")
    response = await client.post(
        "/finance/tags/", json={"name": "Salário", "category_id": cat_id, "type": "income"}
    )
    assert response.status_code == 201
    assert response.json()["type"] == "income"


@pytest.mark.asyncio
async def test_same_category_different_types_allowed(client: AsyncClient):
    """Regra 1: mesma categoria pode ter tags de tipos diferentes."""
    cat_id = await _create_category(client, "Investimentos")
    r1 = await client.post("/finance/tags/", json={"name": "Aporte", "category_id": cat_id, "type": "outcome"})
    r2 = await client.post("/finance/tags/", json={"name": "Resgate", "category_id": cat_id, "type": "income"})
    assert r1.status_code == 201
    assert r2.status_code == 201


@pytest.mark.asyncio
async def test_create_tag_duplicate_returns_409(client: AsyncClient):
    """Não permite criar duas tags com mesmo nome na mesma categoria."""
    cat_id = await _create_category(client, "DupCat")
    payload = {"name": "DupTag", "category_id": cat_id, "type": "outcome"}
    assert (await client.post("/finance/tags/", json=payload)).status_code == 201
    assert (await client.post("/finance/tags/", json=payload)).status_code == 409


@pytest.mark.asyncio
async def test_same_tag_name_different_categories_allowed(client: AsyncClient):
    """Mesmo nome de tag é permitido em categorias diferentes."""
    cat1 = await _create_category(client, "CatA")
    cat2 = await _create_category(client, "CatB")
    r1 = await client.post("/finance/tags/", json={"name": "Comum", "category_id": cat1, "type": "outcome"})
    r2 = await client.post("/finance/tags/", json={"name": "Comum", "category_id": cat2, "type": "outcome"})
    assert r1.status_code == 201
    assert r2.status_code == 201


@pytest.mark.asyncio
async def test_list_tags_by_category(client: AsyncClient):
    cat_id = await _create_category(client, "Transporte")
    await client.post("/finance/tags/", json={"name": "Uber", "category_id": cat_id, "type": "outcome"})
    response = await client.get(f"/finance/tags/?category_id={cat_id}")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_list_tags_filter_by_type(client: AsyncClient):
    cat_id = await _create_category(client, "Misto")
    await client.post("/finance/tags/", json={"name": "Compra", "category_id": cat_id, "type": "outcome"})
    await client.post("/finance/tags/", json={"name": "Venda", "category_id": cat_id, "type": "income"})

    outcome_tags = await client.get(f"/finance/tags/?category_id={cat_id}&type=outcome")
    income_tags  = await client.get(f"/finance/tags/?category_id={cat_id}&type=income")
    assert all(t["type"] == "outcome" for t in outcome_tags.json())
    assert all(t["type"] == "income"  for t in income_tags.json())


@pytest.mark.asyncio
async def test_tag_single_family_via_category(client: AsyncClient):
    """Regra 2: tag pertence a exatamente uma família (via categoria)."""
    fam1 = (await client.post("/finance/tag-families/", json={"name": "Família A"})).json()["id"]
    fam2 = (await client.post("/finance/tag-families/", json={"name": "Família B"})).json()["id"]

    cat_res = await client.post("/finance/categories/", json={"name": "Cat Fam1", "family_id": fam1})
    cat_id = cat_res.json()["id"]
    tag_res = await client.post("/finance/tags/", json={"name": "Minha Tag", "category_id": cat_id, "type": "outcome"})
    assert tag_res.status_code == 201

    # Mudar a categoria para outra família: a tag segue a categoria
    await client.patch(f"/finance/categories/{cat_id}", json={"family_id": fam2})
    tag_after = await client.get(f"/finance/tags/{tag_res.json()['id']}")
    # tag ainda existe, mas agora sua categoria está na fam2 — sem conflito
    assert tag_after.status_code == 200

    # Não é possível ter a mesma tag em duas famílias ao mesmo tempo
    # (constraint estrutural: tag → 1 category → 1 family_id)
    cat2_res = await client.post("/finance/categories/", json={"name": "Cat Fam2", "family_id": fam2})
    dup = await client.post(
        "/finance/tags/",
        json={"name": "Minha Tag", "category_id": cat2_res.json()["id"], "type": "outcome"},
    )
    # Tags com mesmo nome em categorias diferentes são permitidas —
    # o que não é permitido é que a mesma tag (id) exista em 2 famílias
    assert dup.status_code == 201
    assert dup.json()["id"] != tag_res.json()["id"]


@pytest.mark.asyncio
async def test_deactivate_tag(client: AsyncClient):
    cat_id = await _create_category(client, "Misc")
    create = await client.post("/finance/tags/", json={"name": "OldTag", "category_id": cat_id, "type": "outcome"})
    tag_id = create.json()["id"]
    response = await client.patch(f"/finance/tags/{tag_id}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient):
    cat_id = await _create_category(client, "Temp")
    create = await client.post("/finance/tags/", json={"name": "TempTag", "category_id": cat_id, "type": "outcome"})
    tag_id = create.json()["id"]
    assert (await client.delete(f"/finance/tags/{tag_id}")).status_code == 204
