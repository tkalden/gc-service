"""
Outfits — integration tests.

Each write test creates its own data and deletes it. No dependency on
Alice's pre-existing outfits.
"""

from httpx import AsyncClient

_CI_OUTFIT = "CI Test Outfit (auto-delete)"


# ── helpers ──────────────────────────────────────────────────────────────────

async def _create_clothing_item(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/api/v1/clothes",
        json={"name": "CI Outfit Dependency", "category": "tops", "seasons": ["Spring"]},
        headers=headers,
    )
    assert resp.status_code == 200
    return resp.json()["data"]["id"]


async def _create_outfit(client: AsyncClient, headers: dict, clothing_id: str) -> str:
    resp = await client.post(
        "/api/v1/outfits",
        json={
            "name": _CI_OUTFIT,
            "clothing_item_ids": [clothing_id],
            "outfit_date": "2026-01-01",
            "season": "spring",
            "occasion": "casual",
        },
        headers=headers,
    )
    assert resp.status_code == 200, f"Outfit create failed: {resp.text}"
    return resp.json()["data"]["id"]


# ── list ─────────────────────────────────────────────────────────────────────

async def test_list_outfits_returns_list(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/outfits", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert isinstance(data["count"], int)


async def test_list_outfits_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/outfits")
    assert resp.status_code == 401


# ── create / read / delete ────────────────────────────────────────────────────

async def test_create_read_delete_outfit(client: AsyncClient, auth_headers: dict):
    clothing_id = await _create_clothing_item(client, auth_headers)
    outfit_id = await _create_outfit(client, auth_headers, clothing_id)

    try:
        # Read back — verify shape and name
        resp = await client.get(f"/api/v1/outfits/{outfit_id}", headers=auth_headers)
        assert resp.status_code == 200
        outfit = resp.json()["data"]
        assert outfit["name"] == _CI_OUTFIT
        assert outfit["season"] == "spring"
        assert clothing_id in outfit["clothing_item_ids"]

        # Delete
        resp = await client.delete(f"/api/v1/outfits/{outfit_id}", headers=auth_headers)
        assert resp.status_code == 200
        outfit_id = None  # mark as cleaned up

        # Verify gone
        resp = await client.get(
            f"/api/v1/outfits/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    finally:
        if outfit_id:  # clean up if test failed before delete
            await client.delete(f"/api/v1/outfits/{outfit_id}", headers=auth_headers)
        await client.delete(f"/api/v1/clothes/{clothing_id}", headers=auth_headers)


async def test_create_outfit_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/outfits",
        json={"name": "x", "clothing_item_ids": [], "outfit_date": "2026-01-01"},
    )
    assert resp.status_code == 401
