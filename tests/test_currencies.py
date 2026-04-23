import pytest


def create_currency(client, headers, label="Real Brasileiro", symbol="R$"):
    return client.post(
        "/currencies",
        json={"label": label, "symbol": symbol},
        headers=headers,
    )


# ============================================================
# POST /currencies
# ============================================================


class TestCreateCurrency:
    def test_create_currency_success(self, client, admin_headers):
        response = create_currency(client, admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "Real Brasileiro"
        assert data["symbol"] == "R$"
        assert "id" in data

    def test_create_currency_unauthorized(self, client):
        response = client.post("/currencies", json={"label": "Test", "symbol": "T"})
        assert response.status_code == 401

    def test_create_currency_empty_label(self, client, admin_headers):
        response = client.post(
            "/currencies",
            json={"label": "   ", "symbol": "R$"},
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_create_currency_empty_symbol(self, client, admin_headers):
        response = client.post(
            "/currencies",
            json={"label": "Real", "symbol": "  "},
            headers=admin_headers,
        )
        assert response.status_code == 422


# ============================================================
# GET /currencies
# ============================================================


class TestListCurrencies:
    def test_list_currencies_empty(self, client, admin_headers):
        response = client.get("/currencies", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_currencies_returns_all_currencies(
        self, client, admin_headers, user_headers
    ):
        create_currency(client, admin_headers, label="Dólar", symbol="US$")
        create_currency(client, user_headers, label="Euro", symbol="€")

        response = client.get("/currencies", headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_currencies_unauthorized(self, client):
        response = client.get("/currencies")
        assert response.status_code == 401


# ============================================================
# GET /currencies/:id
# ============================================================


class TestGetCurrency:
    def test_get_currency_by_id(self, client, admin_headers):
        created = create_currency(client, admin_headers).json()
        response = client.get(f"/currencies/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_currency_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/currencies/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_currency_unauthorized(self, client, admin_headers):
        created = create_currency(client, admin_headers).json()
        response = client.get(f"/currencies/{created['id']}")
        assert response.status_code == 401


# ============================================================
# PATCH /currencies/:id
# ============================================================


class TestUpdateCurrency:
    def test_update_currency_label(self, client, admin_headers):
        created = create_currency(client, admin_headers).json()
        response = client.patch(
            f"/currencies/{created['id']}",
            json={"label": "Dólar Americano"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Dólar Americano"

    def test_update_currency_symbol(self, client, admin_headers):
        created = create_currency(client, admin_headers, symbol="US$").json()
        response = client.patch(
            f"/currencies/{created['id']}",
            json={"symbol": "USD"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["symbol"] == "USD"

    def test_update_currency_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/currencies/{fake_id}",
            json={"label": "Nope"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_currency_unauthorized(self, client, admin_headers):
        created = create_currency(client, admin_headers).json()
        response = client.patch(
            f"/currencies/{created['id']}",
            json={"label": "Nope"},
        )
        assert response.status_code == 401


# ============================================================
# DELETE /currencies/:id
# ============================================================


class TestDeleteCurrency:
    def test_delete_currency(self, client, admin_headers):
        created = create_currency(client, admin_headers).json()
        response = client.delete(f"/currencies/{created['id']}", headers=admin_headers)
        assert response.status_code == 204

        response = client.get(f"/currencies/{created['id']}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_currency_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/currencies/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_currency_unauthorized(self, client, admin_headers):
        created = create_currency(client, admin_headers).json()
        response = client.delete(f"/currencies/{created['id']}")
        assert response.status_code == 401
