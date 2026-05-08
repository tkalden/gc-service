"""
Shared fixtures for integration tests.

All tests hit the real FastAPI app via an in-process ASGI client.
External services:
  - Supabase auth/DB/storage: real (uses env vars from .env or CI secrets)
  - Replicate VTO API: mocked (slow + costs money)
  - rembg / TensorFlow: real (local, fast)

Supabase resilience: if Supabase is unreachable, `access_token` calls
pytest.skip(), which cascades through every fixture that depends on it
(auth_headers → all protected-endpoint tests). Health tests are unaffected.
CI stays green with a clear "skipped: Supabase unavailable" message.
"""

import base64
import io
import os

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image

from config.settings import get_settings
from main import app

TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "")
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "")


def _check_supabase_reachable() -> None:
    """Raise pytest.skip if Supabase can't be reached within 5 seconds."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        pytest.skip("SUPABASE_URL / SUPABASE_SERVICE_KEY not set — skipping Supabase-dependent tests")
    try:
        resp = httpx.get(
            f"{settings.supabase_url}/rest/v1/",
            headers={"apikey": settings.supabase_service_key},
            timeout=5.0,
        )
        if resp.status_code >= 500:
            pytest.skip(
                f"Supabase returned {resp.status_code} — skipping Supabase-dependent tests"
            )
    except (httpx.ConnectError, httpx.UnsupportedProtocol):
        pytest.skip("Supabase not reachable — skipping Supabase-dependent tests")
    except httpx.TimeoutException:
        pytest.skip("Supabase timed out — skipping Supabase-dependent tests")


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as c:
        yield c


@pytest_asyncio.fixture(scope="session")
async def access_token(client: AsyncClient) -> str:
    _check_supabase_reachable()  # skip entire session if Supabase is down
    if not TEST_EMAIL or not TEST_PASSWORD:
        pytest.skip("TEST_USER_EMAIL / TEST_USER_PASSWORD not set — skipping auth-dependent tests")

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200, f"Test user login failed: {resp.text}"
    token = resp.json().get("access_token")
    assert token, "No access_token in login response"
    return token


@pytest.fixture
def auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_image_b64() -> str:
    """Small synthetic JPEG as base64 — suitable for bg removal and classification."""
    img = Image.new("RGB", (150, 200), color=(180, 120, 90))
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return base64.b64encode(buf.getvalue()).decode()
