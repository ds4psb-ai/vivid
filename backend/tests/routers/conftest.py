"""Router test configuration and fixtures."""

from typing import Dict

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db, Base


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Create auth headers for test requests."""
    return {
        "X-User-Id": "test-user-123",
        "Authorization": "Bearer test-token",
    }


def get_mock_db():
    """Create a mock database session that returns empty results.

    This simulates an empty database so endpoints return default fallback data.
    """
    mock_db = MagicMock()

    # Create mock result for scalar_one_or_none() -> None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalar.return_value = 0

    # Create mock scalars() that returns empty list
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.get = AsyncMock(return_value=None)  # SQLAlchemy session.get() is async
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


# =============================================================================
# Real Database Session Fixture (for integration tests)
# =============================================================================

# Test database URL - uses SQLite in-memory for speed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """Create a real async database session for integration tests.

    Uses SQLite in-memory database for isolation and speed.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
