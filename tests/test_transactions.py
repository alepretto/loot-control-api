import pytest
from uuid import UUID
from datetime import datetime, timezone


# ============================================================
# Helpers
# ============================================================


def create_account(client, headers, label="Nubank", type="digital", logo=None):
    payload = {"label": label, "type": type}
    if logo is not None:
        payload["logo"] = logo
    return client.post("/accounts", json=payload, headers=headers)


def create_category(client, headers, label="Food", nature="variable"):
    payload = {"label": label, "nature": nature}
    return client.post("/categories", json=payload, headers=headers)


def create_subcategory(client, headers, category_id, label="Restaurants"):
    payload = {"category_id": str(category_id), "label": label}
    return client.post("/subcategories", json=payload, headers=headers)


def create_currency(client, headers, code="BRL", label="Real", symbol="R$"):
    payload = {"code": code, "label": label, "symbol": symbol}
    return client.post("/currencies", json=payload, headers=headers)


def create_transaction(client, headers, subcategory_id, account_id, currency_id,
                       date_transaction=None, type="outcome", description="Test",
                       amount=100.0, payment_methods="pix", statement_id=None):
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
    if statement_id is not None:
        payload["statement_id"] = str(statement_id)
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


# ============================================================
# POST /transactions
# ============================================================


class TestCreateTransaction:
    def test_create_transaction_success(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)

        response = create_transaction(
            client, admin_headers,
            subcategory_id=ctx["subcategory_id"],
            account_id=ctx["account_id"],
            currency_id=ctx["currency_id"],
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Test"
        assert data["amount"] == 100.0
        assert data["type"] == "outcome"
        assert data["payment_methods"] == "pix"
        assert "id" in data
        assert "user_id" in data

    def test_create_transaction_income(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)

        response = create_transaction(
            client, admin_headers,
            subcategory_id=ctx["subcategory_id"],
            account_id=ctx["account_id"],
            currency_id=ctx["currency_id"],
            type="income",
            amount=5000.0,
        )
        assert response.status_code == 201
        assert response.json()["type"] == "income"
        assert response.json()["amount"] == 5000.0

    def test_create_transaction_with_null_description(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)

        response = create_transaction(
            client, admin_headers,
            subcategory_id=ctx["subcategory_id"],
            account_id=ctx["account_id"],
            currency_id=ctx["currency_id"],
            description=None,
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_transaction_unauthorized(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)

        response = client.post(
            "/transactions",
            json={
                "date_transaction": datetime.now(timezone.utc).isoformat(),
                "type": "outcome",
                "subcategory_id": ctx["subcategory_id"],
                "account_id": ctx["account_id"],
                "currency_id": ctx["currency_id"],
                "amount": 100.0,
            }
        )
        assert response.status_code == 401

    def test_create_transaction_invalid_type(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)

        response = client.post(
            "/transactions",
            json={
                "date_transaction": datetime.now(timezone.utc).isoformat(),
                "type": "invalid",
                "subcategory_id": ctx["subcategory_id"],
                "account_id": ctx["account_id"],
                "currency_id": ctx["currency_id"],
                "amount": 100.0,
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_create_transaction_negative_amount(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)

        response = client.post(
            "/transactions",
            json={
                "date_transaction": datetime.now(timezone.utc).isoformat(),
                "type": "outcome",
                "subcategory_id": ctx["subcategory_id"],
                "account_id": ctx["account_id"],
                "currency_id": ctx["currency_id"],
                "amount": -50.0,
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_create_transaction_zero_amount(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)

        response = client.post(
            "/transactions",
            json={
                "date_transaction": datetime.now(timezone.utc).isoformat(),
                "type": "outcome",
                "subcategory_id": ctx["subcategory_id"],
                "account_id": ctx["account_id"],
                "currency_id": ctx["currency_id"],
                "amount": 0,
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_create_transaction_invalid_payment_method(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)

        response = client.post(
            "/transactions",
            json={
                "date_transaction": datetime.now(timezone.utc).isoformat(),
                "type": "outcome",
                "subcategory_id": ctx["subcategory_id"],
                "account_id": ctx["account_id"],
                "currency_id": ctx["currency_id"],
                "amount": 100.0,
                "payment_methods": "boleto",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422


# ============================================================
# GET /transactions
# ============================================================


class TestListTransactions:
    def test_list_transactions_empty(self, client, admin_headers):
        response = client.get("/transactions", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_transactions_returns_only_own(self, client, admin_headers, user_headers):
        admin_ctx = create_full_context(client, admin_headers, currency_code="USD")
        user_ctx = create_full_context(client, user_headers, currency_code="EUR")

        create_transaction(client, admin_headers, **admin_ctx, description="Admin TX")
        create_transaction(client, user_headers, **user_ctx, description="User TX")

        admin_response = client.get("/transactions", headers=admin_headers)
        assert admin_response.status_code == 200
        assert len(admin_response.json()) == 1
        assert admin_response.json()[0]["description"] == "Admin TX"

        user_response = client.get("/transactions", headers=user_headers)
        assert user_response.status_code == 200
        assert len(user_response.json()) == 1
        assert user_response.json()[0]["description"] == "User TX"

    def test_list_transactions_unauthorized(self, client):
        response = client.get("/transactions")
        assert response.status_code == 401


# ============================================================
# GET /transactions/:id
# ============================================================


class TestGetTransaction:
    def test_get_transaction_by_id(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.get(f"/transactions/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_transaction_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/transactions/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_transaction_of_other_user(self, client, admin_headers, user_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.get(f"/transactions/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_get_transaction_unauthorized(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.get(f"/transactions/{created['id']}")
        assert response.status_code == 401


# ============================================================
# PATCH /transactions/:id
# ============================================================


class TestUpdateTransaction:
    def test_update_transaction_amount(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx, amount=100.0).json()

        response = client.patch(
            f"/transactions/{created['id']}",
            json={"amount": 250.0},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["amount"] == 250.0

    def test_update_transaction_description(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.patch(
            f"/transactions/{created['id']}",
            json={"description": "Updated description"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_update_transaction_type(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx, type="outcome").json()

        response = client.patch(
            f"/transactions/{created['id']}",
            json={"type": "income"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["type"] == "income"

    def test_update_transaction_payment_methods(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx, payment_methods="pix").json()

        response = client.patch(
            f"/transactions/{created['id']}",
            json={"payment_methods": "credit"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["payment_methods"] == "credit"

    def test_update_transaction_of_other_user(self, client, admin_headers, user_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.patch(
            f"/transactions/{created['id']}",
            json={"amount": 999.0},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_update_transaction_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/transactions/{fake_id}",
            json={"amount": 100.0},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_transaction_unauthorized(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.patch(
            f"/transactions/{created['id']}",
            json={"amount": 100.0},
        )
        assert response.status_code == 401


# ============================================================
# DELETE /transactions/:id
# ============================================================


class TestDeleteTransaction:
    def test_delete_transaction(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.delete(f"/transactions/{created['id']}", headers=admin_headers)
        assert response.status_code == 204

        response = client.get(f"/transactions/{created['id']}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_transaction_of_other_user(self, client, admin_headers, user_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.delete(f"/transactions/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_delete_transaction_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/transactions/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_transaction_unauthorized(self, client, admin_headers):
        ctx = create_full_context(client, admin_headers)
        created = create_transaction(client, admin_headers, **ctx).json()

        response = client.delete(f"/transactions/{created['id']}")
        assert response.status_code == 401
