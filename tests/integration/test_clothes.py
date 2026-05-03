"""
Clothing items — integration tests.

Each test that writes data is self-contained: it creates what it needs
and deletes it in the same test. No dependency on Alice's pre-existing items.
"""

import pytest
from httpx import AsyncClient

_CI_NAME = "CI Test Shirt (auto-delete)"


# ── helpers ──────────────────────────────────────────────────────────────────

async def _create_item(client: AsyncClient, headers: dict, name: str = _CI_NAME) -> str:
    resp = await client.post(
        "/api/v1/clothes",
        json={"name": name, "category": "tops", "seasons": ["Spring"]},
        headers=headers,
    )
    assert resp.status_code == 200, f"Setup failed: {resp.text}"
    return resp.json()["data"]["id"]


async def _delete_item(client: AsyncClient, headers: dict, item_id: str) -> None:
    await client.delete(f"/api/v1/clothes/{item_id}", headers=headers)


# ── list ─────────────────────────────────────────────────────────────────────

async def test_list_clothes_returns_list(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/clothes", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert isinstance(data["count"], int)
    assert data["count"] == len(data["data"])


async def test_list_clothes_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/clothes")
    assert resp.status_code == 401


# ── create ───────────────────────────────────────────────────────────────────

async def test_create_clothing_item(client: AsyncClient, auth_headers: dict):
    item_id = await _create_item(client, auth_headers)
    try:
        assert item_id
    finally:
        await _delete_item(client, auth_headers, item_id)


async def test_create_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/clothes",
        json={"name": "x", "category": "tops", "seasons": ["Spring"]},
    )
    assert resp.status_code == 401


async def test_create_rejects_invalid_category(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/clothes",
        json={"name": "x", "category": "hats", "seasons": ["Spring"]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_create_rejects_empty_seasons(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/clothes",
        json={"name": "x", "category": "tops", "seasons": []},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ── read ─────────────────────────────────────────────────────────────────────

async def test_get_own_item(client: AsyncClient, auth_headers: dict):
    item_id = await _create_item(client, auth_headers)
    try:
        resp = await client.get(f"/api/v1/clothes/{item_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == item_id
        assert resp.json()["data"]["name"] == _CI_NAME
    finally:
        await _delete_item(client, auth_headers, item_id)


async def test_get_item_requires_auth(client: AsyncClient, auth_headers: dict):
    item_id = await _create_item(client, auth_headers)
    try:
        resp = await client.get(f"/api/v1/clothes/{item_id}")
        assert resp.status_code == 401
    finally:
        await _delete_item(client, auth_headers, item_id)


async def test_get_nonexistent_item_returns_404(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/clothes/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── update ───────────────────────────────────────────────────────────────────

async def test_update_own_item(client: AsyncClient, auth_headers: dict):
    item_id = await _create_item(client, auth_headers)
    try:
        resp = await client.put(
            f"/api/v1/clothes/{item_id}",
            json={"name": "Updated Name", "seasons": ["Fall", "Winter"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        updated = resp.json()["data"]
        assert updated["name"] == "Updated Name"
        assert set(updated["seasons"]) == {"Fall", "Winter"}
    finally:
        await _delete_item(client, auth_headers, item_id)


async def test_update_requires_auth(client: AsyncClient, auth_headers: dict):
    item_id = await _create_item(client, auth_headers)
    try:
        resp = await client.put(
            f"/api/v1/clothes/{item_id}",
            json={"name": "Hacked"},
        )
        assert resp.status_code == 401
    finally:
        await _delete_item(client, auth_headers, item_id)


# ── delete ───────────────────────────────────────────────────────────────────

async def test_delete_own_item(client: AsyncClient, auth_headers: dict):
    item_id = await _create_item(client, auth_headers)
    resp = await client.delete(f"/api/v1/clothes/{item_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify it's actually gone
    resp = await client.get(f"/api/v1/clothes/{item_id}", headers=auth_headers)
    assert resp.status_code == 404


async def test_delete_requires_auth(client: AsyncClient, auth_headers: dict):
    item_id = await _create_item(client, auth_headers)
    try:
        resp = await client.delete(f"/api/v1/clothes/{item_id}")
        assert resp.status_code == 401
    finally:
        await _delete_item(client, auth_headers, item_id)
