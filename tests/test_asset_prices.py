import pytest
from uuid import uuid4


# ============================================================
# Helpers
# ============================================================


def create_asset_price(client, headers, symbol="PETR4.SA", price_date="2026-04-24", price=38.50, currency="BRL"):
    return client.post(
        "/asset-prices",
        json={"symbol": symbol, "price_date": price_date, "price": price, "currency": currency},
        headers=headers,
    )


# ============================================================
# POST /asset-prices
# ============================================================


class TestCreateAssetPrice:
    def test_create_asset_price_success(self, client, user_headers):
        response = create_asset_price(client, user_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "PETR4.SA"
        assert data["price"] == 38.50
        assert data["currency"] == "BRL"
        assert data["price_date"] == "2026-04-24"
        assert "id" in data
        assert "created_at" in data

    def test_create_asset_price_with_custom_currency(self, client, user_headers):
        response = create_asset_price(client, user_headers, symbol="AAPL", price=150.0, currency="USD")
        assert response.status_code == 201
        assert response.json()["currency"] == "USD"

    def test_create_asset_price_unauthorized(self, client):
        response = client.post(
            "/asset-prices",
            json={"symbol": "PETR4.SA", "price_date": "2026-04-24", "price": 38.50},
        )
        assert response.status_code == 401

    def test_create_asset_price_missing_required_fields(self, client, user_headers):
        response = client.post(
            "/asset-prices",
            json={},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_asset_price_missing_symbol(self, client, user_headers):
        response = client.post(
            "/asset-prices",
            json={"price_date": "2026-04-24", "price": 38.50},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_asset_price_missing_price_date(self, client, user_headers):
        response = client.post(
            "/asset-prices",
            json={"symbol": "PETR4.SA", "price": 38.50},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_asset_price_missing_price(self, client, user_headers):
        response = client.post(
            "/asset-prices",
            json={"symbol": "PETR4.SA", "price_date": "2026-04-24"},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_asset_price_non_positive_price(self, client, user_headers):
        response = client.post(
            "/asset-prices",
            json={"symbol": "PETR4.SA", "price_date": "2026-04-24", "price": 0},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_asset_price_negative_price(self, client, user_headers):
        response = client.post(
            "/asset-prices",
            json={"symbol": "PETR4.SA", "price_date": "2026-04-24", "price": -10.0},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_asset_price_empty_symbol(self, client, user_headers):
        response = client.post(
            "/asset-prices",
            json={"symbol": "   ", "price_date": "2026-04-24", "price": 38.50},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_asset_price_duplicate_symbol_date(self, client, user_headers):
        """Upsert: same symbol+date updates price instead of error."""
        create_asset_price(client, user_headers, symbol="VALE3.SA", price_date="2026-04-24", price=65.0)
        response = client.post(
            "/asset-prices",
            json={"symbol": "VALE3.SA", "price_date": "2026-04-24", "price": 66.0},
            headers=user_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "VALE3.SA"
        assert data["price_date"] == "2026-04-24"
        assert data["price"] == 66.0


# ============================================================
# GET /asset-prices
# ============================================================


class TestListAssetPrices:
    def test_list_asset_prices_empty(self, client, user_headers):
        response = client.get("/asset-prices", headers=user_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_asset_prices_returns_created(self, client, user_headers):
        create_asset_price(client, user_headers, symbol="PETR4.SA", price=38.50)
        create_asset_price(client, user_headers, symbol="VALE3.SA", price=65.0)

        response = client.get("/asset-prices", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_asset_prices_filtered_by_symbol(self, client, user_headers):
        create_asset_price(client, user_headers, symbol="PETR4.SA", price=38.50)
        create_asset_price(client, user_headers, symbol="VALE3.SA", price=65.0)

        response = client.get("/asset-prices?symbol=PETR4.SA", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "PETR4.SA"

    def test_list_asset_prices_unauthorized(self, client):
        response = client.get("/asset-prices")
        assert response.status_code == 401


# ============================================================
# GET /asset-prices/latest
# ============================================================


class TestGetLatestAssetPrice:
    def test_get_latest_by_symbol(self, client, user_headers):
        create_asset_price(client, user_headers, symbol="PETR4.SA", price_date="2026-04-22", price=37.00)
        create_asset_price(client, user_headers, symbol="PETR4.SA", price_date="2026-04-24", price=38.50)

        response = client.get("/asset-prices/latest?symbol=PETR4.SA", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "PETR4.SA"
        assert data["price"] == 38.50
        assert data["price_date"] == "2026-04-24"

    def test_get_latest_nonexistent_symbol(self, client, user_headers):
        response = client.get("/asset-prices/latest?symbol=NONEXIST.SA", headers=user_headers)
        assert response.status_code == 404

    def test_get_latest_unauthorized(self, client):
        response = client.get("/asset-prices/latest?symbol=PETR4.SA")
        assert response.status_code == 401


# ============================================================
# GET /asset-prices/:id
# ============================================================


class TestGetAssetPrice:
    def test_get_asset_price_by_id(self, client, user_headers):
        created = create_asset_price(client, user_headers).json()
        response = client.get(f"/asset-prices/{created['id']}", headers=user_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_asset_price_not_found(self, client, user_headers):
        fake_id = str(uuid4())
        response = client.get(f"/asset-prices/{fake_id}", headers=user_headers)
        assert response.status_code == 404

    def test_get_asset_price_unauthorized(self, client, user_headers):
        created = create_asset_price(client, user_headers).json()
        response = client.get(f"/asset-prices/{created['id']}")
        assert response.status_code == 401


# ============================================================
# DELETE /asset-prices/:id
# ============================================================


class TestDeleteAssetPrice:
    def test_delete_asset_price(self, client, user_headers):
        created = create_asset_price(client, user_headers).json()
        response = client.delete(f"/asset-prices/{created['id']}", headers=user_headers)
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/asset-prices/{created['id']}", headers=user_headers)
        assert response.status_code == 404

    def test_delete_asset_price_not_found(self, client, user_headers):
        fake_id = str(uuid4())
        response = client.delete(f"/asset-prices/{fake_id}", headers=user_headers)
        assert response.status_code == 404

    def test_delete_asset_price_unauthorized(self, client, user_headers):
        created = create_asset_price(client, user_headers).json()
        response = client.delete(f"/asset-prices/{created['id']}")
        assert response.status_code == 401