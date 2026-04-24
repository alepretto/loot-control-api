import pytest
from datetime import datetime, timezone


# ============================================================
# Helpers
# ============================================================


def create_account(client, headers, label="Nubank", type="digital", logo=None):
    payload = {"label": label, "type": type}
    if logo is not None:
        payload["logo"] = logo
    return client.post("/accounts", json=payload, headers=headers)


def create_credit_card(client, headers, account_id, label="Nubank Gold", due_date=15, end_date_offset=5, is_active=True):
    payload = {"account_id": str(account_id), "label": label, "due_date": due_date, "end_date_offset": end_date_offset, "is_active": is_active}
    return client.post("/credit-cards", json=payload, headers=headers)


def create_statement(client, headers, credit_card_id, end_date=None, is_paid=False, total_amount=None):
    if end_date is None:
        end_date = datetime(2025, 12, 15, tzinfo=timezone.utc).isoformat()
    payload = {"credit_card_id": str(credit_card_id), "end_date": end_date, "is_paid": is_paid}
    if total_amount is not None:
        payload["total_amount"] = total_amount
    return client.post("/credit-card-statements", json=payload, headers=headers)


# ============================================================
# POST /credit-card-statements
# ============================================================


class TestCreateStatement:
    def test_create_statement_success(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()

        response = create_statement(client, admin_headers, credit_card["id"])
        assert response.status_code == 201
        data = response.json()
        assert data["credit_card_id"] == credit_card["id"]
        assert data["is_paid"] is False
        assert data["total_amount"] is None
        assert "id" in data
        assert "user_id" in data
        assert "end_date" in data

    def test_create_statement_with_amount(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()

        response = create_statement(client, admin_headers, credit_card["id"], total_amount=1500.50)
        assert response.status_code == 201
        assert response.json()["total_amount"] == 1500.50

    def test_create_statement_paid(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()

        response = create_statement(client, admin_headers, credit_card["id"], is_paid=True)
        assert response.status_code == 201
        assert response.json()["is_paid"] is True

    def test_create_statement_unauthorized(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()

        response = client.post(
            "/credit-card-statements",
            json={"credit_card_id": str(credit_card["id"]), "end_date": "2025-12-15T00:00:00Z"}
        )
        assert response.status_code == 401

    def test_create_statement_missing_end_date(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()

        response = client.post(
            "/credit-card-statements",
            json={"credit_card_id": str(credit_card["id"])},
            headers=admin_headers
        )
        assert response.status_code == 422


# ============================================================
# GET /credit-card-statements
# ============================================================


class TestListStatements:
    def test_list_statements_empty(self, client, admin_headers):
        response = client.get("/credit-card-statements", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_statements_returns_only_own(self, client, admin_headers, user_headers):
        admin_account = create_account(client, admin_headers).json()
        user_account = create_account(client, user_headers).json()

        admin_cc = create_credit_card(client, admin_headers, admin_account["id"]).json()
        user_cc = create_credit_card(client, user_headers, user_account["id"]).json()

        create_statement(client, admin_headers, admin_cc["id"], total_amount=1000)
        create_statement(client, user_headers, user_cc["id"], total_amount=2000)

        admin_response = client.get("/credit-card-statements", headers=admin_headers)
        assert admin_response.status_code == 200
        assert len(admin_response.json()) == 1
        assert admin_response.json()[0]["total_amount"] == 1000

        user_response = client.get("/credit-card-statements", headers=user_headers)
        assert user_response.status_code == 200
        assert len(user_response.json()) == 1
        assert user_response.json()[0]["total_amount"] == 2000

    def test_list_statements_unauthorized(self, client):
        response = client.get("/credit-card-statements")
        assert response.status_code == 401


# ============================================================
# GET /credit-card-statements/:id
# ============================================================


class TestGetStatement:
    def test_get_statement_by_id(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.get(f"/credit-card-statements/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_statement_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/credit-card-statements/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_statement_of_other_user(self, client, admin_headers, user_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.get(f"/credit-card-statements/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_get_statement_unauthorized(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.get(f"/credit-card-statements/{created['id']}")
        assert response.status_code == 401


# ============================================================
# PATCH /credit-card-statements/:id
# ============================================================


class TestUpdateStatement:
    def test_update_statement_is_paid(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"], is_paid=False).json()

        response = client.patch(
            f"/credit-card-statements/{created['id']}",
            json={"is_paid": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_paid"] is True

    def test_update_statement_total_amount(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.patch(
            f"/credit-card-statements/{created['id']}",
            json={"total_amount": 2500.00},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["total_amount"] == 2500.00

    def test_update_statement_end_date(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        new_date = datetime(2026, 1, 15, tzinfo=timezone.utc).isoformat()
        response = client.patch(
            f"/credit-card-statements/{created['id']}",
            json={"end_date": new_date},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "2026-01-15" in response.json()["end_date"]

    def test_update_statement_of_other_user(self, client, admin_headers, user_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.patch(
            f"/credit-card-statements/{created['id']}",
            json={"is_paid": True},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_update_statement_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/credit-card-statements/{fake_id}",
            json={"is_paid": True},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_statement_unauthorized(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.patch(
            f"/credit-card-statements/{created['id']}",
            json={"is_paid": True},
        )
        assert response.status_code == 401


# ============================================================
# DELETE /credit-card-statements/:id
# ============================================================


class TestDeleteStatement:
    def test_delete_statement(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.delete(f"/credit-card-statements/{created['id']}", headers=admin_headers)
        assert response.status_code == 204

        response = client.get(f"/credit-card-statements/{created['id']}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_statement_of_other_user(self, client, admin_headers, user_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.delete(f"/credit-card-statements/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_delete_statement_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/credit-card-statements/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_statement_unauthorized(self, client, admin_headers):
        account = create_account(client, admin_headers).json()
        credit_card = create_credit_card(client, admin_headers, account["id"]).json()
        created = create_statement(client, admin_headers, credit_card["id"]).json()

        response = client.delete(f"/credit-card-statements/{created['id']}")
        assert response.status_code == 401
