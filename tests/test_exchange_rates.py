from uuid import uuid4


# ============================================================
# Helpers
# ============================================================


def create_exchange_rate(client, headers, from_currency="USD", to_currency="BRL", rate_date="2026-04-24", rate=5.25):
    return client.post(
        "/exchange-rates",
        json={"from_currency": from_currency, "to_currency": to_currency, "rate_date": rate_date, "rate": rate},
        headers=headers,
    )


# ============================================================
# POST /exchange-rates
# ============================================================


class TestCreateExchangeRate:
    def test_create_exchange_rate_success(self, client, user_headers):
        response = create_exchange_rate(client, user_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "BRL"
        assert data["rate"] == 5.25
        assert data["rate_date"] == "2026-04-24"
        assert "id" in data
        assert "created_at" in data

    def test_create_exchange_rate_default_to_currency(self, client, user_headers):
        response = client.post(
            "/exchange-rates",
            json={"from_currency": "EUR", "rate_date": "2026-04-24", "rate": 6.10},
            headers=user_headers,
        )
        assert response.status_code == 201
        assert response.json()["to_currency"] == "BRL"

    def test_create_exchange_rate_unauthorized(self, client):
        response = client.post(
            "/exchange-rates",
            json={"from_currency": "USD", "to_currency": "BRL", "rate_date": "2026-04-24", "rate": 5.25},
        )
        assert response.status_code == 401

    def test_create_exchange_rate_non_positive_rate(self, client, user_headers):
        response = create_exchange_rate(client, user_headers, rate=0)
        assert response.status_code == 422

    def test_create_exchange_rate_negative_rate(self, client, user_headers):
        response = create_exchange_rate(client, user_headers, rate=-1.5)
        assert response.status_code == 422

    def test_create_exchange_rate_empty_from_currency(self, client, user_headers):
        response = client.post(
            "/exchange-rates",
            json={"from_currency": "   ", "to_currency": "BRL", "rate_date": "2026-04-24", "rate": 5.25},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_exchange_rate_empty_to_currency(self, client, user_headers):
        response = client.post(
            "/exchange-rates",
            json={"from_currency": "USD", "to_currency": "   ", "rate_date": "2026-04-24", "rate": 5.25},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_create_exchange_rate_missing_required_fields(self, client, user_headers):
        response = client.post("/exchange-rates", json={}, headers=user_headers)
        assert response.status_code == 422

    def test_create_exchange_rate_currency_uppercased(self, client, user_headers):
        response = client.post(
            "/exchange-rates",
            json={"from_currency": "usd", "to_currency": "brl", "rate_date": "2026-04-24", "rate": 5.25},
            headers=user_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "BRL"


# ============================================================
# GET /exchange-rates
# ============================================================


class TestListExchangeRates:
    def test_list_exchange_rates_empty(self, client, user_headers):
        response = client.get("/exchange-rates", headers=user_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_exchange_rates_returns_created(self, client, user_headers):
        create_exchange_rate(client, user_headers, from_currency="USD", rate=5.25)
        create_exchange_rate(client, user_headers, from_currency="EUR", rate=6.10)

        response = client.get("/exchange-rates", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_exchange_rates_filtered_by_from_currency(self, client, user_headers):
        create_exchange_rate(client, user_headers, from_currency="USD", rate=5.25)
        create_exchange_rate(client, user_headers, from_currency="EUR", rate=6.10)

        response = client.get("/exchange-rates?from_currency=USD", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["from_currency"] == "USD"

    def test_list_exchange_rates_filtered_by_to_currency(self, client, user_headers):
        create_exchange_rate(client, user_headers, from_currency="USD", to_currency="BRL", rate=5.25)
        create_exchange_rate(client, user_headers, from_currency="USD", to_currency="EUR", rate=0.92)

        response = client.get("/exchange-rates?to_currency=BRL", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["to_currency"] == "BRL"

    def test_list_exchange_rates_filtered_by_both(self, client, user_headers):
        create_exchange_rate(client, user_headers, from_currency="USD", to_currency="BRL", rate=5.25)
        create_exchange_rate(client, user_headers, from_currency="EUR", to_currency="BRL", rate=6.10)
        create_exchange_rate(client, user_headers, from_currency="USD", to_currency="EUR", rate=0.92)

        response = client.get("/exchange-rates?from_currency=USD&to_currency=BRL", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["from_currency"] == "USD"
        assert data[0]["to_currency"] == "BRL"

    def test_list_exchange_rates_unauthorized(self, client):
        response = client.get("/exchange-rates")
        assert response.status_code == 401


# ============================================================
# GET /exchange-rates/latest
# ============================================================


class TestGetLatestRate:
    def test_get_latest_rate(self, client, user_headers):
        create_exchange_rate(client, user_headers, from_currency="USD", to_currency="BRL", rate_date="2026-04-22", rate=5.20)
        create_exchange_rate(client, user_headers, from_currency="USD", to_currency="BRL", rate_date="2026-04-24", rate=5.25)

        response = client.get("/exchange-rates/latest?from_currency=USD&to_currency=BRL", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["rate"] == 5.25
        assert data["rate_date"] == "2026-04-24"

    def test_get_latest_rate_not_found(self, client, user_headers):
        response = client.get("/exchange-rates/latest?from_currency=XYZ&to_currency=BRL", headers=user_headers)
        assert response.status_code == 404

    def test_get_latest_rate_unauthorized(self, client):
        response = client.get("/exchange-rates/latest?from_currency=USD&to_currency=BRL")
        assert response.status_code == 401


# ============================================================
# GET /exchange-rates/on-date
# ============================================================


class TestGetRateOnDate:
    def test_get_rate_on_date(self, client, user_headers):
        create_exchange_rate(client, user_headers, from_currency="USD", to_currency="BRL", rate_date="2026-04-24", rate=5.25)

        response = client.get(
            "/exchange-rates/on-date?from_currency=USD&to_currency=BRL&rate_date=2026-04-24",
            headers=user_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rate"] == 5.25
        assert data["rate_date"] == "2026-04-24"

    def test_get_rate_on_date_not_found(self, client, user_headers):
        create_exchange_rate(client, user_headers, from_currency="USD", to_currency="BRL", rate_date="2026-04-24", rate=5.25)

        response = client.get(
            "/exchange-rates/on-date?from_currency=USD&to_currency=BRL&rate_date=2026-04-25",
            headers=user_headers,
        )
        assert response.status_code == 404

    def test_get_rate_on_date_unauthorized(self, client):
        response = client.get("/exchange-rates/on-date?from_currency=USD&to_currency=BRL&rate_date=2026-04-24")
        assert response.status_code == 401


# ============================================================
# GET /exchange-rates/:id
# ============================================================


class TestGetExchangeRate:
    def test_get_exchange_rate_by_id(self, client, user_headers):
        created = create_exchange_rate(client, user_headers).json()
        response = client.get(f"/exchange-rates/{created['id']}", headers=user_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_exchange_rate_not_found(self, client, user_headers):
        fake_id = str(uuid4())
        response = client.get(f"/exchange-rates/{fake_id}", headers=user_headers)
        assert response.status_code == 404

    def test_get_exchange_rate_unauthorized(self, client, user_headers):
        created = create_exchange_rate(client, user_headers).json()
        response = client.get(f"/exchange-rates/{created['id']}")
        assert response.status_code == 401


# ============================================================
# DELETE /exchange-rates/:id
# ============================================================


class TestDeleteExchangeRate:
    def test_delete_exchange_rate(self, client, user_headers):
        created = create_exchange_rate(client, user_headers).json()
        response = client.delete(f"/exchange-rates/{created['id']}", headers=user_headers)
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/exchange-rates/{created['id']}", headers=user_headers)
        assert response.status_code == 404

    def test_delete_exchange_rate_not_found(self, client, user_headers):
        fake_id = str(uuid4())
        response = client.delete(f"/exchange-rates/{fake_id}", headers=user_headers)
        assert response.status_code == 404

    def test_delete_exchange_rate_unauthorized(self, client, user_headers):
        created = create_exchange_rate(client, user_headers).json()
        response = client.delete(f"/exchange-rates/{created['id']}")
        assert response.status_code == 401