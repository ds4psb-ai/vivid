"""Regression tests for scene-detect preview HEAD support."""

import os
import tempfile
import time
import uuid

import pytest
from httpx import AsyncClient

from app import main as app_main
from app.routers import scene_detect


@pytest.fixture(autouse=True)
def cleanup_preview_store():
    """Keep preview store isolated between tests."""
    scene_detect._preview_store.clear()
    yield
    for path, _ in list(scene_detect._preview_store.values()):
        try:
            os.unlink(path)
        except OSError:
            pass
    scene_detect._preview_store.clear()


def test_cors_methods_include_head():
    """CORS method allowlist must include HEAD to avoid preflight failures."""
    assert "HEAD" in app_main.CORS_ALLOWED_METHODS


@pytest.mark.asyncio
async def test_preview_head_returns_not_405(async_client: AsyncClient):
    """HEAD on preview endpoint should be routed (404 is acceptable for missing id)."""
    response = await async_client.head("/api/v1/scene-detect/preview/missing-preview-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_preview_head_existing_returns_success(async_client: AsyncClient):
    """HEAD on an existing preview id should return success with range metadata."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(b"\x00\x00\x00\x20ftypisom")
        preview_path = tmp.name

    preview_id = "test-preview-id"
    scene_detect._preview_store[preview_id] = (preview_path, time.time())

    response = await async_client.head(f"/api/v1/scene-detect/preview/{preview_id}")
    assert response.status_code == 200
    assert response.headers.get("accept-ranges") == "bytes"


@pytest.mark.asyncio
async def test_preview_head_resolves_temp_file_without_store(async_client: AsyncClient):
    """Store miss 상황에서도 deterministic preview path가 있으면 응답 가능해야 한다."""
    preview_id = str(uuid.uuid4())
    preview_path = os.path.join(tempfile.gettempdir(), f"preview_{preview_id}.mp4")

    with open(preview_path, "wb") as fp:
        fp.write(b"\x00\x00\x00\x20ftypisom")

    try:
        response = await async_client.head(f"/api/v1/scene-detect/preview/{preview_id}")
        assert response.status_code == 200
        assert response.headers.get("accept-ranges") == "bytes"
    finally:
        try:
            os.unlink(preview_path)
        except OSError:
            pass
