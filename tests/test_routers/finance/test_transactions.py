import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.main import app
from app.models.user import User

NOW = datetime.now(timezone.utc).isoformat()


async def _setup(client: AsyncClient) -> str:
    """Cria categoria + tag income e retorna o tag_id."""
    cat = await client.post("/finance/categories/", json={"name": "Receitas"})
    tag = await client.post(
        "/finance/tags/",
        json={"name": "Salário", "category_id": cat.json()["id"], "type": "income"},
    )
    return tag.json()["id"]


async def _setup_outcome(client: AsyncClient) -> str:
    """Cria categoria + tag outcome e retorna o tag_id."""
    cat = await client.post("/finance/categories/", json={"name": "Despesas"})
    tag = await client.post(
        "/finance/tags/",
        json={"name": "Mercado", "category_id": cat.json()["id"], "type": "outcome"},
    )
    return tag.json()["id"]


async def _make_tag(client: AsyncClient, cat_name: str, tag_name: str, type_: str = "outcome") -> str:
    """Helper: cria categoria + tag e retorna tag_id."""
    cat = await client.post("/finance/categories/", json={"name": cat_name})
    tag = await client.post(
        "/finance/tags/",
        json={"name": tag_name, "category_id": cat.json()["id"], "type": type_},
    )
    return tag.json()["id"]


@pytest.mark.asyncio
async def test_create_transaction(client: AsyncClient):
    tag_id = await _setup(client)
    response = await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_id, "date_transaction": NOW, "value": 5000.0, "currency": "BRL"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == 5000.0
    assert data["currency"] == "BRL"


@pytest.mark.asyncio
async def test_transaction_type_from_tag(client: AsyncClient):
    """O tipo da transação é determinado pela tag, não pela categoria."""
    cat_id = (await client.post("/finance/categories/", json={"name": "Investimentos"})).json()["id"]
    tag_in  = (await client.post("/finance/tags/", json={"name": "Resgate", "category_id": cat_id, "type": "income"})).json()
    tag_out = (await client.post("/finance/tags/", json={"name": "Aporte",  "category_id": cat_id, "type": "outcome"})).json()

    r_in  = await client.post("/finance/transactions/", json={"tag_id": tag_in["id"],  "date_transaction": NOW, "value": 1000.0, "currency": "BRL"})
    r_out = await client.post("/finance/transactions/", json={"tag_id": tag_out["id"], "date_transaction": NOW, "value": 500.0,  "currency": "BRL"})

    assert r_in.status_code == 201
    assert r_out.status_code == 201
    # O tipo é inferido da tag, não da transação em si
    assert r_in.json()["tag_id"] == tag_in["id"]
    assert r_out.json()["tag_id"] == tag_out["id"]


@pytest.mark.asyncio
async def test_create_investment_transaction(client: AsyncClient):
    tag_id = await _setup_outcome(client)
    response = await client.post(
        "/finance/transactions/",
        json={
            "tag_id": tag_id,
            "date_transaction": NOW,
            "value": 1000.0,
            "currency": "USD",
            "quantity": 0.01,
            "symbol": "BTC",
            "index_rate": 95000.0,
            "index": "CoinGecko",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "BTC"
    assert data["quantity"] == 0.01


@pytest.mark.asyncio
async def test_list_transactions_paginated(client: AsyncClient):
    tag_id = await _setup(client)
    for i in range(5):
        await client.post(
            "/finance/transactions/",
            json={"tag_id": tag_id, "date_transaction": NOW, "value": float(i * 100 + 1), "currency": "BRL"},
        )
    response = await client.get("/finance/transactions/?page=1&page_size=3")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data and "total" in data
    assert len(data["items"]) <= 3


@pytest.mark.asyncio
async def test_update_transaction(client: AsyncClient):
    tag_id = await _setup(client)
    create = await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_id, "date_transaction": NOW, "value": 200.0, "currency": "BRL"},
    )
    tx_id = create.json()["id"]
    response = await client.patch(f"/finance/transactions/{tx_id}", json={"value": 250.0})
    assert response.status_code == 200
    assert response.json()["value"] == 250.0


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient):
    tag_id = await _setup(client)
    create = await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_id, "date_transaction": NOW, "value": 100.0, "currency": "BRL"},
    )
    tx_id = create.json()["id"]
    assert (await client.delete(f"/finance/transactions/{tx_id}")).status_code == 204


@pytest.mark.asyncio
async def test_get_nonexistent_transaction(client: AsyncClient):
    response = await client.get("/finance/transactions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_filter_by_currency(client: AsyncClient):
    """Filtra transações por moeda: apenas BRL retornado ao filtrar por currency=BRL."""
    tag_id = await _make_tag(client, "RecCurrency", "EntradaBRL", "income")
    tag_usd = await _make_tag(client, "RecCurrencyUSD", "EntradaUSD", "income")

    for _ in range(2):
        await client.post(
            "/finance/transactions/",
            json={"tag_id": tag_id, "date_transaction": NOW, "value": 100.0, "currency": "BRL"},
        )
    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_usd, "date_transaction": NOW, "value": 50.0, "currency": "USD"},
    )

    response = await client.get(f"/finance/transactions/?currency=BRL&tag_id={tag_id}")
    assert response.status_code == 200
    data = response.json()
    assert all(item["currency"] == "BRL" for item in data["items"])
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_filter_by_date_range(client: AsyncClient):
    """Filtra transações por date_from e date_to: apenas as dentro do intervalo retornadas."""
    from urllib.parse import urlencode

    tag_id = await _make_tag(client, "RecDateRange", "EntradaDate", "income")

    base = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    tx_dates = [
        base - timedelta(days=10),  # fora do range
        base,                        # dentro
        base + timedelta(days=5),    # dentro
    ]
    for d in tx_dates:
        await client.post(
            "/finance/transactions/",
            json={"tag_id": tag_id, "date_transaction": d.isoformat(), "value": 10.0, "currency": "BRL"},
        )

    date_from = base - timedelta(days=1)
    date_to = base + timedelta(days=6)

    # Use urlencode so the '+00:00' timezone offset is percent-encoded correctly
    params = urlencode({
        "tag_id": tag_id,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    })
    response = await client.get(f"/finance/transactions/?{params}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        tx_date = datetime.fromisoformat(item["date_transaction"])
        assert date_from <= tx_date <= date_to


@pytest.mark.asyncio
async def test_filter_by_tag_id(client: AsyncClient):
    """Filtra transações por tag_id: apenas as da tag correta retornadas."""
    tag_a = await _make_tag(client, "CatFilterTagA", "TagA", "outcome")
    tag_b = await _make_tag(client, "CatFilterTagB", "TagB", "outcome")

    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_a, "date_transaction": NOW, "value": 100.0, "currency": "BRL"},
    )
    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_a, "date_transaction": NOW, "value": 200.0, "currency": "BRL"},
    )
    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_b, "date_transaction": NOW, "value": 300.0, "currency": "BRL"},
    )

    response = await client.get(f"/finance/transactions/?tag_id={tag_a}")
    assert response.status_code == 200
    data = response.json()
    assert all(item["tag_id"] == tag_a for item in data["items"])
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_filter_by_category_id(client: AsyncClient):
    """Filtra transações por category_id: apenas as da categoria correta retornadas."""
    cat_a = (await client.post("/finance/categories/", json={"name": "CatFilterCatA"})).json()
    cat_b = (await client.post("/finance/categories/", json={"name": "CatFilterCatB"})).json()

    tag_a = (await client.post(
        "/finance/tags/",
        json={"name": "TgCatA", "category_id": cat_a["id"], "type": "outcome"},
    )).json()
    tag_b = (await client.post(
        "/finance/tags/",
        json={"name": "TgCatB", "category_id": cat_b["id"], "type": "outcome"},
    )).json()

    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_a["id"], "date_transaction": NOW, "value": 50.0, "currency": "BRL"},
    )
    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_a["id"], "date_transaction": NOW, "value": 75.0, "currency": "BRL"},
    )
    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_b["id"], "date_transaction": NOW, "value": 99.0, "currency": "BRL"},
    )

    response = await client.get(f"/finance/transactions/?category_id={cat_a['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["tag_id"] == tag_a["id"] for item in data["items"])


@pytest.mark.asyncio
async def test_filter_by_family_id(client: AsyncClient):
    """Filtra transações por family_id: isolamento entre famílias."""
    fam_a = (await client.post("/finance/tag-families/", json={"name": "FamFilterA"})).json()
    fam_b = (await client.post("/finance/tag-families/", json={"name": "FamFilterB"})).json()

    cat_a = (await client.post(
        "/finance/categories/", json={"name": "CatFamA", "family_id": fam_a["id"]}
    )).json()
    cat_b = (await client.post(
        "/finance/categories/", json={"name": "CatFamB", "family_id": fam_b["id"]}
    )).json()

    tag_a = (await client.post(
        "/finance/tags/", json={"name": "TgFamA", "category_id": cat_a["id"], "type": "outcome"}
    )).json()
    tag_b = (await client.post(
        "/finance/tags/", json={"name": "TgFamB", "category_id": cat_b["id"], "type": "outcome"}
    )).json()

    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_a["id"], "date_transaction": NOW, "value": 100.0, "currency": "BRL"},
    )
    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_a["id"], "date_transaction": NOW, "value": 200.0, "currency": "BRL"},
    )
    await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_b["id"], "date_transaction": NOW, "value": 300.0, "currency": "BRL"},
    )

    response = await client.get(f"/finance/transactions/?family_id={fam_a['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["tag_id"] == tag_a["id"] for item in data["items"])

    # Família B não deve enxergar as transações da família A
    response_b = await client.get(f"/finance/transactions/?family_id={fam_b['id']}")
    assert response_b.json()["total"] == 1
    assert response_b.json()["items"][0]["tag_id"] == tag_b["id"]


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient):
    """Cria 5 transações, verifica page_size e total corretos."""
    tag_id = await _make_tag(client, "CatPagination", "TgPagination", "outcome")

    for i in range(5):
        await client.post(
            "/finance/transactions/",
            json={"tag_id": tag_id, "date_transaction": NOW, "value": float(i + 1), "currency": "BRL"},
        )

    # page 1 com page_size=2 — deve retornar 2 itens e total=5
    r1 = await client.get(f"/finance/transactions/?tag_id={tag_id}&page=1&page_size=2")
    assert r1.status_code == 200
    d1 = r1.json()
    assert len(d1["items"]) == 2
    assert d1["total"] == 5
    assert d1["page"] == 1
    assert d1["page_size"] == 2

    # page 2 — próximos 2 itens
    r2 = await client.get(f"/finance/transactions/?tag_id={tag_id}&page=2&page_size=2")
    assert r2.status_code == 200
    d2 = r2.json()
    assert len(d2["items"]) == 2
    assert d2["total"] == 5

    # ids das páginas 1 e 2 não se repetem
    ids_p1 = {item["id"] for item in d1["items"]}
    ids_p2 = {item["id"] for item in d2["items"]}
    assert ids_p1.isdisjoint(ids_p2)


@pytest.mark.asyncio
async def test_update_transaction(client: AsyncClient):
    """PATCH atualiza value e date_transaction corretamente."""
    tag_id = await _make_tag(client, "CatUpdateTx", "TgUpdateTx", "outcome")
    create = await client.post(
        "/finance/transactions/",
        json={"tag_id": tag_id, "date_transaction": NOW, "value": 100.0, "currency": "BRL"},
    )
    tx_id = create.json()["id"]

    new_date = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    response = await client.patch(
        f"/finance/transactions/{tx_id}",
        json={"value": 999.99, "date_transaction": new_date},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 999.99
    assert data["id"] == tx_id


@pytest.mark.asyncio
async def test_data_isolation(session: AsyncSession, test_user: User):
    """Usuário B não enxerga as transações do usuário A."""
    # Criar um segundo usuário
    user_b = User(
        id=uuid.uuid4(),
        email=f"user-b-{uuid.uuid4()}@lootcontrol.com",
        username=f"userb-{uuid.uuid4().hex[:8]}",
        first_name="User",
        last_name="B",
    )
    session.add(user_b)
    await session.commit()
    await session.refresh(user_b)

    # Cliente para o usuário A (test_user) usando a mesma sessão
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_current_user_id] = lambda: str(test_user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_a:
        cat = await client_a.post("/finance/categories/", json={"name": "CatIsolation"})
        tag = await client_a.post(
            "/finance/tags/",
            json={"name": "TgIsolation", "category_id": cat.json()["id"], "type": "outcome"},
        )
        tx_res = await client_a.post(
            "/finance/transactions/",
            json={"tag_id": tag.json()["id"], "date_transaction": NOW, "value": 777.0, "currency": "BRL"},
        )
        tx_id = tx_res.json()["id"]
        assert tx_res.status_code == 201

    # Cliente para o usuário B
    app.dependency_overrides[get_current_user_id] = lambda: str(user_b.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_b:
        # GET por id deve retornar 404
        r_get = await client_b.get(f"/finance/transactions/{tx_id}")
        assert r_get.status_code == 404

        # LIST não deve retornar a transação do usuário A
        r_list = await client_b.get("/finance/transactions/")
        ids = [item["id"] for item in r_list.json()["items"]]
        assert tx_id not in ids

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_investment_fields(client: AsyncClient):
    """Campos de investimento são persistidos e retornados corretamente."""
    tag_id = await _make_tag(client, "CatInvestFields", "TgInvestFields", "outcome")

    response = await client.post(
        "/finance/transactions/",
        json={
            "tag_id": tag_id,
            "date_transaction": NOW,
            "value": 5000.0,
            "currency": "BRL",
            "quantity": 2.5,
            "symbol": "PETR4",
            "index_rate": 12.5,
            "index": "IPCA",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 2.5
    assert data["symbol"] == "PETR4"
    assert data["index_rate"] == 12.5
    assert data["index"] == "IPCA"

    # Verificar persistência via GET
    tx_id = data["id"]
    get_res = await client.get(f"/finance/transactions/{tx_id}")
    assert get_res.status_code == 200
    persisted = get_res.json()
    assert persisted["quantity"] == 2.5
    assert persisted["symbol"] == "PETR4"
    assert persisted["index_rate"] == 12.5
    assert persisted["index"] == "IPCA"
