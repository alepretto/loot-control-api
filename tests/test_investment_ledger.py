from uuid import UUID
from datetime import datetime, timezone


# ============================================================
# Helpers (mirrors test_transactions.py patterns)
# ============================================================


def create_account(client, headers, label="Nubank", type="digital", logo=None):
    payload = {"label": label, "type": type}
    if logo is not None:
        payload["logo"] = logo
    return client.post("/accounts", json=payload, headers=headers)


def create_category(client, headers, label="Investments", nature="investment"):
    payload = {"label": label, "nature": nature}
    return client.post("/categories", json=payload, headers=headers)


def create_subcategory(client, headers, category_id, label="Stocks"):
    payload = {"category_id": str(category_id), "label": label}
    return client.post("/subcategories", json=payload, headers=headers)


def create_currency(client, headers, code="BRL", label="Real", symbol="R$"):
    payload = {"code": code, "label": label, "symbol": symbol}
    return client.post("/currencies", json=payload, headers=headers)


def create_transaction(client, headers, subcategory_id, account_id, currency_id,
                       date_transaction=None, type="outcome", description="Investment",
                       amount=1000.0, payment_methods="pix"):
    payload = {
        "date_transaction": (date_transaction or datetime.now(timezone.utc).isoformat()),
        "type": type,
        "subcategory_id": str(subcategory_id),
        "account_id": str(account_id),
        "currency_id": str(currency_id),
        "description": description,
        "amount": amount,
        "payment_methods": payment_methods,
    }
    return client.post("/transactions", json=payload, headers=headers)


def create_full_context(client, headers, currency_code="BRL"):
    """Create account + category + subcategory + currency and return IDs."""
    account = create_account(client, headers).json()
    category = create_category(client, headers).json()
    subcategory = create_subcategory(client, headers, category["id"]).json()
    currency = create_currency(client, headers, code=currency_code).json()
    return {
        "account_id": account["id"],
        "subcategory_id": subcategory["id"],
        "currency_id": currency["id"],
    }


def create_investment(client, headers, transaction_id, symbol="PETR4", quantity=10.0, index=None, index_rate=None):
    payload = {
        "transaction_id": str(transaction_id),
        "symbol": symbol,
        "quantity": quantity,
    }
    if index is not None:
        payload["index"] = index
    if index_rate is not None:
        payload["index_rate"] = index_rate
    return client.post("/investments", json=payload, headers=headers)


# ============================================================
# POST /investments
# ============================================================


class TestCreateInvestment:
    def test_create_investment_success(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx)
        assert tx.status_code == 201, f"Transaction setup failed: {tx.text}"
        tx_id = tx.json()["id"]

        response = create_investment(client, admin_headers, transaction_id=tx_id)
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "PETR4"
        assert data["quantity"] == 10.0
        assert data["index"] is None
        assert data["index_rate"] is None
        assert "id" in data
        assert "user_id" in data
        assert data["transaction_id"] == tx_id

    def test_create_investment_with_index(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx)
        tx_id = tx.json()["id"]

        response = create_investment(
            client, admin_headers, transaction_id=tx_id, symbol="BOVA11",
            quantity=5.0, index="IBOV", index_rate=0.01,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "BOVA11"
        assert data["quantity"] == 5.0
        assert data["index"] == "IBOV"
        assert data["index_rate"] == 0.01

    def test_create_investment_unauthorized(self, client):
        response = client.post(
            "/investments",
            json={"transaction_id": "00000000-0000-0000-0000-000000000000", "symbol": "PETR4", "quantity": 10},
        )
        assert response.status_code == 401

    def test_create_investment_empty_symbol(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx)
        tx_id = tx.json()["id"]

        response = client.post(
            "/investments",
            json={"transaction_id": str(tx_id), "symbol": "   ", "quantity": 10},
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_create_investment_negative_quantity(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx)
        tx_id = tx.json()["id"]

        response = client.post(
            "/investments",
            json={"transaction_id": str(tx_id), "symbol": "PETR4", "quantity": -1},
            headers=admin_headers,
        )
        assert response.status_code == 422


# ============================================================
# GET /investments
# ============================================================


class TestListInvestments:
    def test_list_investments_empty(self, client, admin_headers):
        response = client.get("/investments", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_investments_returns_only_own(self, client, admin_headers, user_headers):
        ctx1 = create_full_context(client, admin_headers, currency_code="USD")
        ctx2 = create_full_context(client, user_headers, currency_code="EUR")

        tx1 = create_transaction(client, admin_headers, **ctx1).json()
        tx2 = create_transaction(client, user_headers, **ctx2).json()

        create_investment(client, admin_headers, transaction_id=tx1["id"], symbol="PETR4")
        create_investment(client, user_headers, transaction_id=tx2["id"], symbol="VALE3")

        admin_response = client.get("/investments", headers=admin_headers)
        assert admin_response.status_code == 200
        assert len(admin_response.json()) == 1
        assert admin_response.json()[0]["symbol"] == "PETR4"

        user_response = client.get("/investments", headers=user_headers)
        assert user_response.status_code == 200
        assert len(user_response.json()) == 1
        assert user_response.json()[0]["symbol"] == "VALE3"

    def test_list_investments_unauthorized(self, client):
        response = client.get("/investments")
        assert response.status_code == 401


# ============================================================
# GET /investments/:id
# ============================================================


class TestGetInvestment:
    def test_get_investment_by_id(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.get(f"/investments/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_investment_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/investments/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_investment_of_other_user(self, client, admin_headers, user_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.get(f"/investments/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_get_investment_unauthorized(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.get(f"/investments/{created['id']}")
        assert response.status_code == 401


# ============================================================
# PATCH /investments/:id
# ============================================================


class TestUpdateInvestment:
    def test_update_investment_symbol(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"], symbol="PETR4").json()

        response = client.patch(
            f"/investments/{created['id']}",
            json={"symbol": "VALE3"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["symbol"] == "VALE3"

    def test_update_investment_quantity(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"], quantity=10.0).json()

        response = client.patch(
            f"/investments/{created['id']}",
            json={"quantity": 20.0},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["quantity"] == 20.0

    def test_update_investment_index(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.patch(
            f"/investments/{created['id']}",
            json={"index": "IBOV", "index_rate": 0.015},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["index"] == "IBOV"
        assert response.json()["index_rate"] == 0.015

    def test_update_investment_of_other_user(self, client, admin_headers, user_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.patch(
            f"/investments/{created['id']}",
            json={"symbol": "Hacked"},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_update_investment_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/investments/{fake_id}",
            json={"symbol": "Nope"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_investment_unauthorized(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.patch(
            f"/investments/{created['id']}",
            json={"symbol": "Nope"},
        )
        assert response.status_code == 401


# ============================================================
# DELETE /investments/:id
# ============================================================


class TestDeleteInvestment:
    def test_delete_investment(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.delete(f"/investments/{created['id']}", headers=admin_headers)
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/investments/{created['id']}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_investment_of_other_user(self, client, admin_headers, user_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.delete(f"/investments/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_delete_investment_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/investments/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_investment_unauthorized(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        tx = create_transaction(client, admin_headers, **ctx).json()
        created = create_investment(client, admin_headers, transaction_id=tx["id"]).json()

        response = client.delete(f"/investments/{created['id']}")
        assert response.status_code == 401
