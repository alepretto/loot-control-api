"""Tests for all user endpoints:
- POST /signup  → Create user
- POST /login   → Login (get JWT)
- GET  /users/me → Get current user
- GET  /users    → List users (admin only)
- GET  /users/:id → Get user by ID (admin only)
"""

from uuid import UUID


class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/signup",
            json={"first_name": "João", "last_name": "Silva", "email": "joao@test.com", "password": "secret123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "João"
        assert data["last_name"] == "Silva"
        assert data["email"] == "joao@test.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        # id must be a valid UUID
        UUID(data["id"])
        assert "password" not in data

    def test_signup_duplicate_email(self, client):
        client.post("/signup", json={"first_name": "A", "last_name": "B", "email": "dup@test.com", "password": "pass123"})
        response = client.post("/signup", json={"first_name": "C", "last_name": "D", "email": "dup@test.com", "password": "pass456"})
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_signup_invalid_email(self, client):
        response = client.post(
            "/signup",
            json={"first_name": "Bad", "last_name": "Email", "email": "not-an-email", "password": "pass123"},
        )
        assert response.status_code == 422

    def test_signup_empty_first_name(self, client):
        response = client.post(
            "/signup",
            json={"first_name": "", "last_name": "Silva", "email": "empty@test.com", "password": "pass123"},
        )
        assert response.status_code == 422

    def test_signup_empty_last_name(self, client):
        response = client.post(
            "/signup",
            json={"first_name": "João", "last_name": "", "email": "empty2@test.com", "password": "pass123"},
        )
        assert response.status_code == 422

    def test_signup_short_password(self, client):
        response = client.post(
            "/signup",
            json={"first_name": "User", "last_name": "Short", "email": "short@test.com", "password": "ab"},
        )
        assert response.status_code == 201


class TestLogin:
    def test_login_success(self, client):
        client.post("/signup", json={"first_name": "Log", "last_name": "In", "email": "log@test.com", "password": "mypass"})
        response = client.post("/login", json={"email": "log@test.com", "password": "mypass"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/signup", json={"first_name": "Wrong", "last_name": "Pass", "email": "wrong@test.com", "password": "right"})
        response = client.post("/login", json={"email": "wrong@test.com", "password": "wrong"})
        assert response.status_code == 401

    def test_login_nonexistent_email(self, client):
        response = client.post("/login", json={"email": "noone@test.com", "password": "pass"})
        assert response.status_code == 401

    def test_login_inactive_user(self, client, session):
        from app.core.security import hash_password
        from app.models.user import User as UserModel

        user = UserModel(
            first_name="Inactive",
            last_name="User",
            email="inactive@test.com",
            password=hash_password("pass123"),
            is_active=False,
        )
        session.add(user)
        session.commit()

        response = client.post("/login", json={"email": "inactive@test.com", "password": "pass123"})
        assert response.status_code == 401


class TestGetMe:
    def test_get_me_success(self, client, user_headers, normal_user):
        response = client.get("/users/me", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(normal_user.id)
        assert data["email"] == normal_user.email
        assert data["first_name"] == normal_user.first_name
        assert data["last_name"] == normal_user.last_name
        assert "password" not in data

    def test_get_me_unauthorized(self, client):
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        response = client.get("/users/me", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401


class TestListUsers:
    def test_list_users_as_admin(self, client, admin_headers, admin_user, normal_user):
        response = client.get("/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        emails = [u["email"] for u in data]
        assert admin_user.email in emails
        assert normal_user.email in emails

    def test_list_users_as_normal_user_forbidden(self, client, user_headers):
        response = client.get("/users", headers=user_headers)
        assert response.status_code == 403

    def test_list_users_unauthorized(self, client):
        response = client.get("/users")
        assert response.status_code == 401


class TestGetUserById:
    def test_get_user_by_id_as_admin(self, client, admin_headers, normal_user):
        response = client.get(f"/users/{normal_user.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(normal_user.id)
        assert data["email"] == normal_user.email
        assert data["first_name"] == normal_user.first_name
        assert data["last_name"] == normal_user.last_name

    def test_get_user_by_id_not_found(self, client, admin_headers):
        # Use a non-existent UUID
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/users/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_get_user_by_id_as_normal_user_forbidden(self, client, user_headers, admin_user):
        response = client.get(f"/users/{admin_user.id}", headers=user_headers)
        assert response.status_code == 403

    def test_get_user_by_id_unauthorized(self, client, admin_user):
        response = client.get(f"/users/{admin_user.id}")
        assert response.status_code == 401