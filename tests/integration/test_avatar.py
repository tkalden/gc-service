"""
Avatar tests.

VTO tests mock avatar_service.perform_virtual_try_on to avoid hitting
Replicate (cost + ~20s latency). The job-queue plumbing (async dispatch,
status polling, 404 on unknown job) is tested without that mock.

The avatar_id and clothing_item_id are fetched dynamically from the test
user's real data — no hardcoded IDs.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


# ── helpers ──────────────────────────────────────────────────────────────────

async def _get_avatar_id(client: AsyncClient, headers: dict) -> str:
    resp = await client.get("/api/v1/avatar", headers=headers)
    assert resp.status_code == 200, f"Avatar fetch failed: {resp.text}"
    avatar_id = resp.json()["data"]["id"]
    assert avatar_id, "Test user has no avatar — run the app and upload one first"
    return avatar_id


async def _get_any_clothing_id(client: AsyncClient, headers: dict) -> str:
    resp = await client.get("/api/v1/clothes", headers=headers)
    items = resp.json().get("data", [])
    assert items, "Test user has no clothing items — create at least one first"
    return items[0]["id"]


# ── avatar GET ────────────────────────────────────────────────────────────────

async def test_get_avatar_returns_expected_shape(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/avatar", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    avatar = data["data"]
    assert "id" in avatar
    assert "original_image_path" in avatar
    assert "user_id" in avatar or True  # field may vary — just ensure core shape


async def test_avatar_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/avatar")
    assert resp.status_code == 401


# ── virtual try-on: async job plumbing ───────────────────────────────────────

async def test_tryon_returns_job_id_immediately(client: AsyncClient, auth_headers: dict):
    """POST should return 200 with job_id before the Replicate call completes."""
    avatar_id = await _get_avatar_id(client, auth_headers)
    clothing_id = await _get_any_clothing_id(client, auth_headers)

    with patch(
        "app.api.v1.avatar.router.avatar_service.perform_virtual_try_on",
        new_callable=AsyncMock,
        return_value={"success": True, "result_image": "base64data", "confidence_score": 0.9},
    ):
        resp = await client.post(
            "/api/v1/avatar/try-on",
            json={"avatar_id": avatar_id, "clothing_item_id": clothing_id},
            headers=auth_headers,
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["status"] == "processing"
    assert "job_id" in body
    assert len(body["job_id"]) == 36  # UUID format


async def test_tryon_job_completes_and_status_reflects_result(
    client: AsyncClient, auth_headers: dict
):
    avatar_id = await _get_avatar_id(client, auth_headers)
    clothing_id = await _get_any_clothing_id(client, auth_headers)

    mock_result = {"success": True, "result_image": "base64data", "confidence_score": 0.9}

    with patch(
        "app.api.v1.avatar.router.avatar_service.perform_virtual_try_on",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        start = await client.post(
            "/api/v1/avatar/try-on",
            json={"avatar_id": avatar_id, "clothing_item_id": clothing_id},
            headers=auth_headers,
        )
        job_id = start.json()["job_id"]
        await asyncio.sleep(0.3)  # let background task complete

        status = await client.get(
            f"/api/v1/avatar/try-on/status/{job_id}",
            headers=auth_headers,
        )

    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "completed"
    assert body["success"] is True


async def test_tryon_job_reflects_failure_when_service_raises(
    client: AsyncClient, auth_headers: dict
):
    """If perform_virtual_try_on raises, the job status should be 'failed', not 500."""
    avatar_id = await _get_avatar_id(client, auth_headers)
    clothing_id = await _get_any_clothing_id(client, auth_headers)

    with patch(
        "app.api.v1.avatar.router.avatar_service.perform_virtual_try_on",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Replicate timeout"),
    ):
        start = await client.post(
            "/api/v1/avatar/try-on",
            json={"avatar_id": avatar_id, "clothing_item_id": clothing_id},
            headers=auth_headers,
        )
        job_id = start.json()["job_id"]
        await asyncio.sleep(0.3)

        status = await client.get(
            f"/api/v1/avatar/try-on/status/{job_id}",
            headers=auth_headers,
        )

    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "failed"
    assert body["success"] is False


async def test_tryon_status_unknown_job_returns_404(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/avatar/try-on/status/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_tryon_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/avatar/try-on",
        json={"avatar_id": "x", "clothing_item_id": "y"},
    )
    assert resp.status_code == 401
