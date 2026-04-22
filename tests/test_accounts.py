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


# ============================================================
# POST /accounts
# ============================================================


class TestCreateAccount:
    def test_create_account_success(self, client, admin_headers):
        response = create_account(client, admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "Nubank"
        assert data["type"] == "digital"
        assert data["logo"] is None
        assert "id" in data
        assert "user_id" in data

    def test_create_account_with_logo(self, client, admin_headers):
        response = create_account(client, admin_headers, label="Itaú", type="bank", logo="itau-logo")
        assert response.status_code == 201
        assert response.json()["logo"] == "itau-logo"

    def test_create_account_all_types(self, client, admin_headers):
        for atype in ("bank", "wallet", "digital", "benefits"):
            response = create_account(client, admin_headers, label=f"Acc-{atype}", type=atype)
            assert response.status_code == 201
            assert response.json()["type"] == atype

    def test_create_account_unauthorized(self, client):
        response = client.post(
            "/accounts", json={"label": "Test", "type": "bank"}
        )
        assert response.status_code == 401

    def test_create_account_empty_label(self, client, admin_headers):
        response = client.post(
            "/accounts", json={"label": "   ", "type": "bank"}, headers=admin_headers
        )
        assert response.status_code == 422

    def test_create_account_invalid_type(self, client, admin_headers):
        response = client.post(
            "/accounts", json={"label": "Test", "type": "invalid"}, headers=admin_headers
        )
        assert response.status_code == 422


# ============================================================
# GET /accounts
# ============================================================


class TestListAccounts:
    def test_list_accounts_empty(self, client, admin_headers):
        response = client.get("/accounts", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_accounts_returns_only_own(self, client, admin_headers, user_headers):
        create_account(client, admin_headers, label="Admin Account")
        create_account(client, user_headers, label="User Account")

        # Admin sees only their own
        admin_response = client.get("/accounts", headers=admin_headers)
        assert admin_response.status_code == 200
        assert len(admin_response.json()) == 1
        assert admin_response.json()[0]["label"] == "Admin Account"

        # User sees only their own
        user_response = client.get("/accounts", headers=user_headers)
        assert user_response.status_code == 200
        assert len(user_response.json()) == 1
        assert user_response.json()[0]["label"] == "User Account"

    def test_list_accounts_unauthorized(self, client):
        response = client.get("/accounts")
        assert response.status_code == 401


# ============================================================
# GET /accounts/:id
# ============================================================


class TestGetAccount:
    def test_get_account_by_id(self, client, admin_headers):
        created = create_account(client, admin_headers).json()
        response = client.get(f"/accounts/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_account_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/accounts/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_account_of_other_user(self, client, admin_headers, user_headers):
        created = create_account(client, admin_headers).json()
        # User tries to access admin's account
        response = client.get(f"/accounts/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_get_account_unauthorized(self, client, admin_headers):
        created = create_account(client, admin_headers).json()
        response = client.get(f"/accounts/{created['id']}")
        assert response.status_code == 401


# ============================================================
# PATCH /accounts/:id
# ============================================================


class TestUpdateAccount:
    def test_update_account_label(self, client, admin_headers):
        created = create_account(client, admin_headers).json()
        response = client.patch(
            f"/accounts/{created['id']}",
            json={"label": "Updated Label"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Updated Label"

    def test_update_account_type(self, client, admin_headers):
        created = create_account(client, admin_headers, type="bank").json()
        response = client.patch(
            f"/accounts/{created['id']}",
            json={"type": "digital"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["type"] == "digital"

    def test_update_account_logo(self, client, admin_headers):
        created = create_account(client, admin_headers).json()
        response = client.patch(
            f"/accounts/{created['id']}",
            json={"logo": "new-logo"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["logo"] == "new-logo"

    def test_update_account_of_other_user(self, client, admin_headers, user_headers):
        created = create_account(client, admin_headers).json()
        response = client.patch(
            f"/accounts/{created['id']}",
            json={"label": "Hacked"},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_update_account_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/accounts/{fake_id}",
            json={"label": "Nope"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_account_unauthorized(self, client, admin_headers):
        created = create_account(client, admin_headers).json()
        response = client.patch(
            f"/accounts/{created['id']}",
            json={"label": "Nope"},
        )
        assert response.status_code == 401


# ============================================================
# DELETE /accounts/:id
# ============================================================


class TestDeleteAccount:
    def test_delete_account(self, client, admin_headers):
        created = create_account(client, admin_headers).json()
        response = client.delete(f"/accounts/{created['id']}", headers=admin_headers)
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/accounts/{created['id']}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_account_of_other_user(self, client, admin_headers, user_headers):
        created = create_account(client, admin_headers).json()
        response = client.delete(f"/accounts/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_delete_account_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/accounts/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_account_unauthorized(self, client, admin_headers):
        created = create_account(client, admin_headers).json()
        response = client.delete(f"/accounts/{created['id']}")
        assert response.status_code == 401