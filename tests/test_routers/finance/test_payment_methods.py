import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_pm(client: AsyncClient, name: str = "Crédito", category: str = "money") -> dict:
    res = await client.post("/finance/payment-methods/", json={"name": name, "category": category})
    assert res.status_code == 201
    return res.json()


async def _create_tag(client: AsyncClient) -> str:
    """Create the minimal tag hierarchy needed for transaction tests."""
    cat = await client.post("/finance/categories/", json={"name": "Alimentação"})
    cat_id = cat.json()["id"]
    tag = await client.post("/finance/tags/", json={"name": "Restaurante", "category_id": cat_id, "type": "outcome"})
    return tag.json()["id"]


# ── CRUD ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_money_method(client: AsyncClient):
    data = await _create_pm(client, "Crédito Nubank", "money")
    assert data["name"] == "Crédito Nubank"
    assert data["category"] == "money"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_benefit_method(client: AsyncClient):
    data = await _create_pm(client, "Vale Refeição", "benefit")
    assert data["category"] == "benefit"


@pytest.mark.asyncio
async def test_create_duplicate_name_returns_409(client: AsyncClient):
    await _create_pm(client, "PIX")
    res = await client.post("/finance/payment-methods/", json={"name": "PIX", "category": "money"})
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_list_all(client: AsyncClient):
    await _create_pm(client, "Débito", "money")
    await _create_pm(client, "Vale Alimentação", "benefit")
    res = await client.get("/finance/payment-methods/")
    assert res.status_code == 200
    names = [m["name"] for m in res.json()]
    assert "Débito" in names
    assert "Vale Alimentação" in names


@pytest.mark.asyncio
async def test_list_filter_active(client: AsyncClient):
    data = await _create_pm(client, "Boleto", "money")
    await client.patch(f"/finance/payment-methods/{data['id']}", json={"is_active": False})

    active = await client.get("/finance/payment-methods/?is_active=true")
    inactive = await client.get("/finance/payment-methods/?is_active=false")

    assert all(m["is_active"] for m in active.json())
    assert any(m["name"] == "Boleto" for m in inactive.json())


@pytest.mark.asyncio
async def test_get_by_id(client: AsyncClient):
    data = await _create_pm(client, "Dinheiro", "money")
    res = await client.get(f"/finance/payment-methods/{data['id']}")
    assert res.status_code == 200
    assert res.json()["name"] == "Dinheiro"


@pytest.mark.asyncio
async def test_get_not_found_returns_404(client: AsyncClient):
    import uuid
    res = await client.get(f"/finance/payment-methods/{uuid.uuid4()}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_name(client: AsyncClient):
    data = await _create_pm(client, "OldName", "money")
    res = await client.patch(f"/finance/payment-methods/{data['id']}", json={"name": "NewName"})
    assert res.status_code == 200
    assert res.json()["name"] == "NewName"


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient):
    data = await _create_pm(client, "Ticket", "money")
    res = await client.patch(f"/finance/payment-methods/{data['id']}", json={"category": "benefit"})
    assert res.status_code == 200
    assert res.json()["category"] == "benefit"


@pytest.mark.asyncio
async def test_deactivate(client: AsyncClient):
    data = await _create_pm(client, "Antigo", "money")
    res = await client.patch(f"/finance/payment-methods/{data['id']}", json={"is_active": False})
    assert res.status_code == 200
    assert res.json()["is_active"] is False


@pytest.mark.asyncio
async def test_reactivate(client: AsyncClient):
    data = await _create_pm(client, "Reativar", "money")
    await client.patch(f"/finance/payment-methods/{data['id']}", json={"is_active": False})
    res = await client.patch(f"/finance/payment-methods/{data['id']}", json={"is_active": True})
    assert res.json()["is_active"] is True


@pytest.mark.asyncio
async def test_delete(client: AsyncClient):
    data = await _create_pm(client, "Temp", "money")
    res = await client.delete(f"/finance/payment-methods/{data['id']}")
    assert res.status_code == 204

    get_res = await client.get(f"/finance/payment-methods/{data['id']}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_not_found_returns_404(client: AsyncClient):
    import uuid
    res = await client.delete(f"/finance/payment-methods/{uuid.uuid4()}")
    assert res.status_code == 404


# ── Integração com transações ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_transaction_with_payment_method(client: AsyncClient):
    """Transação pode ser criada com payment_method_id."""
    pm = await _create_pm(client, "Crédito XP", "money")
    tag_id = await _create_tag(client)

    res = await client.post("/finance/transactions/", json={
        "tag_id": tag_id,
        "date_transaction": "2026-03-30T12:00:00",
        "value": 150.0,
        "currency": "BRL",
        "payment_method_id": pm["id"],
    })
    assert res.status_code == 201
    assert res.json()["payment_method_id"] == pm["id"]


@pytest.mark.asyncio
async def test_transaction_without_payment_method(client: AsyncClient):
    """payment_method_id é opcional — pode ser null."""
    tag_id = await _create_tag(client)

    res = await client.post("/finance/transactions/", json={
        "tag_id": tag_id,
        "date_transaction": "2026-03-30T13:00:00",
        "value": 50.0,
        "currency": "BRL",
    })
    assert res.status_code == 201
    assert res.json()["payment_method_id"] is None


@pytest.mark.asyncio
async def test_update_transaction_payment_method(client: AsyncClient):
    """PATCH pode atribuir ou remover o método de pagamento de uma transação."""
    pm = await _create_pm(client, "PIX Bradesco", "money")
    tag_id = await _create_tag(client)

    tx = (await client.post("/finance/transactions/", json={
        "tag_id": tag_id,
        "date_transaction": "2026-03-30T14:00:00",
        "value": 200.0,
        "currency": "BRL",
    })).json()

    # Atribui método
    patch = await client.patch(f"/finance/transactions/{tx['id']}", json={"payment_method_id": pm["id"]})
    assert patch.status_code == 200
    assert patch.json()["payment_method_id"] == pm["id"]

    # Remove método (null)
    remove = await client.patch(f"/finance/transactions/{tx['id']}", json={"payment_method_id": None})
    assert remove.status_code == 200
    assert remove.json()["payment_method_id"] is None


@pytest.mark.asyncio
async def test_delete_payment_method_sets_null_on_transactions(client: AsyncClient):
    """Excluir um método de pagamento não apaga transações (ON DELETE SET NULL)."""
    pm = await _create_pm(client, "CartaoTemp", "money")
    tag_id = await _create_tag(client)

    tx = (await client.post("/finance/transactions/", json={
        "tag_id": tag_id,
        "date_transaction": "2026-03-30T15:00:00",
        "value": 75.0,
        "currency": "BRL",
        "payment_method_id": pm["id"],
    })).json()

    # Exclui o método
    assert (await client.delete(f"/finance/payment-methods/{pm['id']}")).status_code == 204

    # Transação ainda existe com payment_method_id = null
    get_tx = await client.get(f"/finance/transactions/{tx['id']}")
    assert get_tx.status_code == 200
    assert get_tx.json()["payment_method_id"] is None
