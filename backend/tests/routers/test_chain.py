"""Tests for Chain Session API.

Tests cover:
- CRUD operations for chain sessions
- Optimistic locking (version conflict detection)
- Previous run lookup

Note: These tests use the mock DB which returns empty results.
Full integration tests require a real database setup.
"""

import uuid

import pytest
from httpx import AsyncClient


# =============================================================================
# Get Session Tests (Mock DB returns None = 404)
# =============================================================================

@pytest.mark.asyncio
async def test_get_chain_session_not_found(async_client: AsyncClient):
    """Test 404 when session doesn't exist."""
    fake_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/chain/session/{fake_id}")

    # Mock DB returns None, so should be 404
    assert response.status_code == 404


# =============================================================================
# Update Session Tests
# =============================================================================

@pytest.mark.asyncio
async def test_update_chain_session_not_found(async_client: AsyncClient):
    """Test 404 when session doesn't exist."""
    fake_id = str(uuid.uuid4())
    response = await async_client.put(
        f"/api/v1/chain/session/{fake_id}",
        json={"version": 1, "title": "Test"},
    )

    assert response.status_code == 404


# =============================================================================
# Delete Session Tests
# =============================================================================

@pytest.mark.asyncio
async def test_delete_chain_session_not_found(async_client: AsyncClient):
    """Test 404 when deleting non-existent session."""
    fake_id = str(uuid.uuid4())
    response = await async_client.delete(f"/api/v1/chain/session/{fake_id}")

    assert response.status_code == 404


# =============================================================================
# Schema Validation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_create_session_validates_title_length(async_client: AsyncClient):
    """Test that title max length is enforced (validation error)."""
    long_title = "x" * 300  # Exceeds 255 limit

    response = await async_client.post(
        "/api/v1/chain/session",
        json={"title": long_title},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chain_data_valid_structure_passes_validation(async_client: AsyncClient):
    """Test that valid chain_data structure passes validation."""
    fake_id = str(uuid.uuid4())

    # Valid chain_data structure - should pass Pydantic validation
    # but fail with 404 (session not found)
    response = await async_client.put(
        f"/api/v1/chain/session/{fake_id}",
        json={
            "version": 1,
            "chain_data": {
                "test-dim": {
                    "dimension_key": "test-dim",
                    "output": {"key": "value"},
                    "title": "Test",
                    "evidence_refs": ["db:run:123", "db:run:456"],
                }
            },
        },
    )

    # Should hit 404 (session not found), not 422 (validation)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_uuid_returns_422(async_client: AsyncClient):
    """Test that invalid UUID returns validation error."""
    response = await async_client.get("/api/v1/chain/session/not-a-uuid")

    assert response.status_code == 422  # Invalid UUID format
