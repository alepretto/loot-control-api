import pytest
from uuid import UUID


# ============================================================
# Helpers
# ============================================================


def create_category(client, headers, label="Alimentação", nature="variable"):
    return client.post(
        "/categories",
        json={"label": label, "nature": nature},
        headers=headers,
    )


# ============================================================
# POST /categories
# ============================================================


class TestCreateCategory:
    def test_create_category_success(self, client, admin_headers):
        response = create_category(client, admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "Alimentação"
        assert data["nature"] == "variable"
        assert "id" in data
        assert "user_id" in data

    def test_create_category_all_natures(self, client, admin_headers):
        for nature in ("fixed", "variable", "investment", "revenue"):
            response = create_category(
                client, admin_headers, label=f"Cat-{nature}", nature=nature
            )
            assert response.status_code == 201
            assert response.json()["nature"] == nature

    def test_create_category_unauthorized(self, client):
        response = client.post("/categories", json={"label": "Test", "nature": "fixed"})
        assert response.status_code == 401

    def test_create_category_empty_label(self, client, admin_headers):
        response = client.post(
            "/categories",
            json={"label": "   ", "nature": "fixed"},
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_create_category_invalid_nature(self, client, admin_headers):
        response = client.post(
            "/categories",
            json={"label": "Test", "nature": "invalid"},
            headers=admin_headers,
        )
        assert response.status_code == 422


# ============================================================
# GET /categories
# ============================================================


class TestListCategories:
    def test_list_categories_empty(self, client, admin_headers):
        response = client.get("/categories", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_categories_returns_only_own(
        self, client, admin_headers, user_headers
    ):
        create_category(client, admin_headers, label="Admin Cat")
        create_category(client, user_headers, label="User Cat")

        admin_response = client.get("/categories", headers=admin_headers)
        assert admin_response.status_code == 200
        assert len(admin_response.json()) == 1
        assert admin_response.json()[0]["label"] == "Admin Cat"

        user_response = client.get("/categories", headers=user_headers)
        assert user_response.status_code == 200
        assert len(user_response.json()) == 1
        assert user_response.json()[0]["label"] == "User Cat"

    def test_list_categories_unauthorized(self, client):
        response = client.get("/categories")
        assert response.status_code == 401


# ============================================================
# GET /categories/:id
# ============================================================


class TestGetCategory:
    def test_get_category_by_id(self, client, admin_headers):
        created = create_category(client, admin_headers).json()
        response = client.get(f"/categories/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_category_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/categories/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_category_of_other_user(self, client, admin_headers, user_headers):
        created = create_category(client, admin_headers).json()
        response = client.get(f"/categories/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_get_category_unauthorized(self, client, admin_headers):
        created = create_category(client, admin_headers).json()
        response = client.get(f"/categories/{created['id']}")
        assert response.status_code == 401


# ============================================================
# PATCH /categories/:id
# ============================================================


class TestUpdateCategory:
    def test_update_category_label(self, client, admin_headers):
        created = create_category(client, admin_headers).json()
        response = client.patch(
            f"/categories/{created['id']}",
            json={"label": "Updated Label"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Updated Label"

    def test_update_category_nature(self, client, admin_headers):
        created = create_category(client, admin_headers, nature="fixed").json()
        response = client.patch(
            f"/categories/{created['id']}",
            json={"nature": "variable"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["nature"] == "variable"

    def test_update_category_of_other_user(self, client, admin_headers, user_headers):
        created = create_category(client, admin_headers).json()
        response = client.patch(
            f"/categories/{created['id']}",
            json={"label": "Hacked"},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_update_category_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/categories/{fake_id}",
            json={"label": "Nope"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_category_unauthorized(self, client, admin_headers):
        created = create_category(client, admin_headers).json()
        response = client.patch(
            f"/categories/{created['id']}",
            json={"label": "Nope"},
        )
        assert response.status_code == 401


# ============================================================
# DELETE /categories/:id
# ============================================================


class TestDeleteCategory:
    def test_delete_category(self, client, admin_headers):
        created = create_category(client, admin_headers).json()
        response = client.delete(f"/categories/{created['id']}", headers=admin_headers)
        assert response.status_code == 204

        response = client.get(f"/categories/{created['id']}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_category_of_other_user(self, client, admin_headers, user_headers):
        created = create_category(client, admin_headers).json()
        response = client.delete(f"/categories/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_delete_category_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/categories/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_category_unauthorized(self, client, admin_headers):
        created = create_category(client, admin_headers).json()
        response = client.delete(f"/categories/{created['id']}")
        assert response.status_code == 401
