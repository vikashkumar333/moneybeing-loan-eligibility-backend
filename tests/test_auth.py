import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from models.user import User
from core.security import create_access_token, verify_password

client = TestClient(app)


def test_1_successful_login():
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPassword123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800


def test_2_invalid_username():
    response = client.post("/api/v1/auth/login", json={"username": "unknown_admin", "password": "AnyPassword"})
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Invalid username or password"


def test_3_invalid_password():
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "WrongPassword"})
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Invalid username or password"


def test_4_missing_username():
    response = client.post("/api/v1/auth/login", json={"password": "AdminPassword123"})
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"


def test_5_missing_password():
    response = client.post("/api/v1/auth/login", json={"username": "admin"})
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"


def test_6_inactive_user():
    response = client.post("/api/v1/auth/login", json={"username": "disabled_user", "password": "DisabledPass123"})
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"
    assert "disabled" in data["message"].lower()


def test_7_valid_jwt():
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPassword123"})
    token = login_resp.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_8_invalid_jwt():
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.string"})
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


def test_9_expired_jwt():
    expired_token = create_access_token(
        subject="1",
        claims={"role": "Admin", "username": "admin"},
        expires_delta=timedelta(seconds=-10),
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


def test_10_missing_authorization_header():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


def test_11_malformed_bearer_token():
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Basic YWRtaW46cGFzcw=="})
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


def test_12_admin_can_access_admin_route():
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPassword123"})
    admin_token = login_resp.json()["access_token"]

    response = client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["message"] == "Admin access granted"


def test_13_non_admin_cannot_access_admin_route():
    login_resp = client.post("/api/v1/auth/login", json={"username": "staff", "password": "StaffPassword123"})
    staff_token = login_resp.json()["access_token"]

    response = client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 403
    data = response.json()
    assert data["status"] == "error"
    assert "permission" in data["message"].lower()


def test_14_unauthenticated_user_cannot_access_admin_route():
    response = client.get("/api/v1/auth/admin-check")
    assert response.status_code == 401


def test_15_me_with_valid_token():
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPassword123"})
    token = login_resp.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["username"] == "admin"
    assert data["role"] == "Admin"
    assert data["is_active"] is True


def test_16_me_without_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_17_password_is_stored_as_hash(db):
    user = db.query(User).filter(User.username == "admin").first()
    assert user is not None
    assert user.password_hash != "AdminPassword123"
    assert user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$")
    assert verify_password("AdminPassword123", user.password_hash)


def test_18_password_is_never_returned():
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPassword123"})
    token = login_resp.json()["access_token"]

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    content_str = me_resp.text.lower()
    assert "password" not in me_resp.json()["data"]
    assert "password_hash" not in me_resp.json()["data"]
    assert "adminpassword123" not in content_str


def test_19_logout_success():
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPassword123"})
    token = login_resp.json()["access_token"]

    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Logged out successfully"
