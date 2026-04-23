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


def create_subcategory(client, headers, category_id, label="Restaurante", is_active=True):
    return client.post(
        "/subcategories",
        json={"label": label, "category_id": str(category_id), "is_active": is_active},
        headers=headers,
    )


# ============================================================
# POST /subcategories
# ============================================================


class TestCreateSubcategory:
    def test_create_subcategory_success(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        response = create_subcategory(client, admin_headers, category_id=cat["id"])
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "Restaurante"
        assert data["category_id"] == cat["id"]
        assert data["is_active"] is True
        assert "id" in data
        assert "user_id" in data

    def test_create_subcategory_unauthorized(self, client):
        response = client.post(
            "/subcategories",
            json={"label": "Test", "category_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 401

    def test_create_subcategory_empty_label(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        response = client.post(
            "/subcategories",
            json={"label": "   ", "category_id": cat["id"]},
            headers=admin_headers,
        )
        assert response.status_code == 422


# ============================================================
# GET /subcategories
# ============================================================


class TestListSubcategories:
    def test_list_subcategories_empty(self, client, admin_headers):
        response = client.get("/subcategories", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_subcategories_returns_only_own(
        self, client, admin_headers, user_headers
    ):
        cat_admin = create_category(client, admin_headers, label="Admin Cat").json()
        cat_user = create_category(client, user_headers, label="User Cat").json()
        create_subcategory(client, admin_headers, category_id=cat_admin["id"], label="Admin Sub")
        create_subcategory(client, user_headers, category_id=cat_user["id"], label="User Sub")

        admin_response = client.get("/subcategories", headers=admin_headers)
        assert admin_response.status_code == 200
        assert len(admin_response.json()) == 1
        assert admin_response.json()[0]["label"] == "Admin Sub"

        user_response = client.get("/subcategories", headers=user_headers)
        assert user_response.status_code == 200
        assert len(user_response.json()) == 1
        assert user_response.json()[0]["label"] == "User Sub"

    def test_list_subcategories_unauthorized(self, client):
        response = client.get("/subcategories")
        assert response.status_code == 401


# ============================================================
# GET /subcategories/:id
# ============================================================


class TestGetSubcategory:
    def test_get_subcategory_by_id(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.get(f"/subcategories/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_subcategory_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/subcategories/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_subcategory_of_other_user(self, client, admin_headers, user_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.get(f"/subcategories/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_get_subcategory_unauthorized(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.get(f"/subcategories/{created['id']}")
        assert response.status_code == 401


# ============================================================
# PATCH /subcategories/:id
# ============================================================


class TestUpdateSubcategory:
    def test_update_subcategory_label(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.patch(
            f"/subcategories/{created['id']}",
            json={"label": "Updated Label"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Updated Label"

    def test_update_subcategory_category_id(self, client, admin_headers):
        cat1 = create_category(client, admin_headers, label="Cat1").json()
        cat2 = create_category(client, admin_headers, label="Cat2").json()
        created = create_subcategory(client, admin_headers, category_id=cat1["id"]).json()
        response = client.patch(
            f"/subcategories/{created['id']}",
            json={"category_id": cat2["id"]},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["category_id"] == cat2["id"]

    def test_update_subcategory_is_active(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.patch(
            f"/subcategories/{created['id']}",
            json={"is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_subcategory_of_other_user(self, client, admin_headers, user_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.patch(
            f"/subcategories/{created['id']}",
            json={"label": "Hacked"},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_update_subcategory_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(
            f"/subcategories/{fake_id}",
            json={"label": "Nope"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_update_subcategory_unauthorized(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.patch(
            f"/subcategories/{created['id']}",
            json={"label": "Nope"},
        )
        assert response.status_code == 401


# ============================================================
# DELETE /subcategories/:id
# ============================================================


class TestDeleteSubcategory:
    def test_delete_subcategory(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.delete(f"/subcategories/{created['id']}", headers=admin_headers)
        assert response.status_code == 204

        response = client.get(f"/subcategories/{created['id']}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_subcategory_of_other_user(self, client, admin_headers, user_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.delete(f"/subcategories/{created['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_delete_subcategory_not_found(self, client, admin_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/subcategories/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_subcategory_unauthorized(self, client, admin_headers):
        cat = create_category(client, admin_headers).json()
        created = create_subcategory(client, admin_headers, category_id=cat["id"]).json()
        response = client.delete(f"/subcategories/{created['id']}")
        assert response.status_code == 401
