"""MCP test configuration and fixtures."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db


def get_mock_db():
    """Create a mock database session."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.rollback = AsyncMock()
    return mock_db


@pytest_asyncio.fixture
async def async_client():
    """Create async test client with mocked database and auth header."""
    mock_db = get_mock_db()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    # Include X-User-Id header for dev auth bypass
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-User-Id": "test-user-123"},
    ) as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_async_client():
    """Create async test client with admin privileges."""
    mock_db = get_mock_db()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    # Include both X-User-Id and X-Admin-Mode headers for admin access
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={
            "X-User-Id": "admin-user-456",
            "X-Admin-Mode": "true",
        },
    ) as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()
