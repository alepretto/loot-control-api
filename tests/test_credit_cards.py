import pytest
from uuid import UUID


# ============================================================
# Helpers
# ============================================================


def create_account(client, headers, label="Nubank", type="digital", logo=None):
    payload = {"label": label, "type": type}
    if logo is not None:
        payload["logo"] = logo
    return client.post("/accounts", json=payload, headers=headers)


def create_credit_card(client, headers, account_id, label=" Nubank Gold", due_date=15, end_date_offset=5, is_active=True):
    payload = {"account_id": str(account_id), "label": label, "due_date": due_date, "end_date_offset": end_date_offset, "is_active": is_active}
    return client.post("/credit-cards", json=payload, headers=headers)


# ============================================================
# POST /credit-cards
# ============================================================


class TestCreateCreditCard:
    def test_create_credit_card_success(self, client, admin_headers):
        # First create an account to reference
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        response = create_credit_card(client, admin_headers, account_id)
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == " Nubank Gold"
        assert data["due_date"] == 15
        assert data["end_date_offset"] == 5
        assert data["is_active"] is True
        assert "id" in data
        assert "user_id" in data
        assert "account_id" in data

    def test_create_credit_card_with_all_fields(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        response = create_credit_card(
            client, admin_headers,
            account_id,
            label="Itaú Platinum",
            due_date=20,
            end_date_offset=10,
            is_active=False
        )
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "Itaú Platinum"
        assert data["due_date"] == 20
        assert data["end_date_offset"] == 10
        assert data["is_active"] is False

    def test_create_credit_card_unauthorized(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        response = client.post(
            "/credit-cards",
            json={"account_id": str(account_id), "label": "Test", "due_date": 10, "end_date_offset": 5}
        )
        assert response.status_code == 401

    def test_create_credit_card_empty_label(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        response = client.post(
            "/credit-cards",
            json={"account_id": str(account_id), "label": "   ", "due_date": 10, "end_date_offset": 5},
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_create_credit_card_invalid_due_date(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        response = client.post(
            "/credit-cards",
            json={"account_id": str(account_id), "label": "Test", "due_date": 32, "end_date_offset": 5},
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_create_credit_card_invalid_end_date_offset(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        response = client.post(
            "/credit-cards",
            json={"account_id": str(account_id), "label": "Test", "due_date": 10, "end_date_offset": 16},
            headers=admin_headers
        )
        assert response.status_code == 422


# ============================================================
# GET /credit-cards
# ============================================================


class TestListCreditCards:
    def test_list_credit_cards_empty(self, client, admin_headers):
        response = client.get("/credit-cards", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_credit_cards_returns_only_own(self, client, admin_headers, user_headers):
        # Create accounts first
        admin_account = create_account(client, admin_headers, label="Admin Account").json()
        user_account = create_account(client, user_headers, label="User Account").json()

        # Create credit cards
        create_credit_card(client, admin_headers, admin_account["id"], label="Admin Card")
        create_credit_card(client, user_headers, user_account["id"], label="User Card")

        # Admin sees only their own
        admin_response = client.get("/credit-cards", headers=admin_headers)
        assert admin_response.status_code == 200
        assert len(admin_response.json()) == 1
        assert admin_response.json()[0]["label"] == "Admin Card"

        # User sees only their own
        user_response = client.get("/credit-cards", headers=user_headers)
        assert user_response.status_code == 200
        assert len(user_response.json()) == 1
        assert user_response.json()[0]["label"] == "User Card"

    def test_list_credit_cards_unauthorized(self, client):
        response = client.get("/credit-cards")
        assert response.status_code == 401


# ============================================================
# GET /credit-cards/:id
# ============================================================


class TestGetCreditCard:
    def test_get_credit_card_by_id(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        response = client.get(f"/credit-cards/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_credit_card_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/credit-cards/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_credit_card_of_other_user(self, client, admin_headers, user_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        # User tries to access admin's credit card
        response = client.get(f"/credit-cards/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_get_credit_card_unauthorized(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        response = client.get(f"/credit-cards/{created['id']}")
        assert response.status_code == 401


# ============================================================
# PATCH /credit-cards/:id
# ============================================================


class TestUpdateCreditCard:
    def test_update_credit_card_label(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        response = client.patch(
            f"/credit-cards/{created['id']}",
            json={"label": "Updated Label"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Updated Label"

    def test_update_credit_card_due_date(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id, due_date=10).json()
        response = client.patch(
            f"/credit-cards/{created['id']}",
            json={"due_date": 25},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["due_date"] == 25

    def test_update_credit_card_end_date_offset(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id, end_date_offset=5).json()
        response = client.patch(
            f"/credit-cards/{created['id']}",
            json={"end_date_offset": 10},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["end_date_offset"] == 10

    def test_update_credit_card_is_active(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id, is_active=True).json()
        response = client.patch(
            f"/credit-cards/{created['id']}",
            json={"is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_credit_card_of_other_user(self, client, admin_headers, user_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        response = client.patch(
            f"/credit-cards/{created['id']}",
            json={"label": "Hacked"},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_update_credit_card_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/credit-cards/{fake_id}",
            json={"label": "Nope"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_credit_card_unauthorized(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        response = client.patch(
            f"/credit-cards/{created['id']}",
            json={"label": "Nope"},
        )
        assert response.status_code == 401


# ============================================================
# DELETE /credit-cards/:id
# ============================================================


class TestDeleteCreditCard:
    def test_delete_credit_card(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        response = client.delete(f"/credit-cards/{created['id']}", headers=admin_headers)
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/credit-cards/{created['id']}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_credit_card_of_other_user(self, client, admin_headers, user_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        response = client.delete(f"/credit-cards/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_delete_credit_card_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/credit-cards/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_credit_card_unauthorized(self, client, admin_headers):
        account_response = create_account(client, admin_headers)
        account_id = account_response.json()["id"]

        created = create_credit_card(client, admin_headers, account_id).json()
        response = client.delete(f"/credit-cards/{created['id']}")
        assert response.status_code == 401