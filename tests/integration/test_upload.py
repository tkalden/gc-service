from httpx import AsyncClient


async def test_smart_upload_background_removal_and_classification(
    client: AsyncClient, auth_headers: dict, sample_image_b64: str
):
    resp = await client.post(
        "/api/v1/upload/smart-upload-async",
        json={"image_base64": sample_image_b64},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    result = data["data"]
    assert result["background_removed"] is True
    assert result["image_base64"]  # processed image present
    assert result["category"] is not None  # classifier returned a category


async def test_smart_upload_requires_auth(client: AsyncClient, sample_image_b64: str):
    resp = await client.post(
        "/api/v1/upload/smart-upload-async",
        json={"image_base64": sample_image_b64},
    )
    assert resp.status_code == 401


async def test_smart_upload_rejects_missing_image(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.post(
        "/api/v1/upload/smart-upload-async",
        json={},
        headers=auth_headers,
    )
    assert resp.status_code == 400
