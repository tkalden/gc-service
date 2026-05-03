import pytest
from httpx import AsyncClient


async def test_login_success(client: AsyncClient, access_token: str):
    # access_token fixture already validates login — just verify the value
    assert access_token.startswith("ey")  # JWT format


async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test-user@example.com", "password": "definitely_wrong"},
    )
    # Supabase returns 400 for bad credentials (not 401)
    assert resp.status_code in (400, 401)


async def test_login_unknown_user(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent.ci.user@gmail.com", "password": "anything"},
    )
    assert resp.status_code in (400, 401)


async def test_me_returns_user_info(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    # /me returns user info under "user" key
    user = data["user"]
    assert "email" in user
    assert user["email"] == "test-user@example.com"


async def test_protected_endpoint_requires_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_invalid_token_rejected(client: AsyncClient):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer notavalidtoken"},
    )
    assert resp.status_code == 401
