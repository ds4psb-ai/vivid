"""
Database setup (async SQLAlchemy + asyncpg)
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.ENVIRONMENT == "development",
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for models"""
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(drop_all: bool = False) -> None:
    """Initialize database. If drop_all=True, drop all tables first (dev only)."""
    async with engine.begin() as conn:
        if drop_all:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("ALTER TABLE canvases ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1")
        )
        await conn.execute(
            text("ALTER TABLE canvases ADD COLUMN IF NOT EXISTS owner_id VARCHAR(160)")
        )
        await conn.execute(
            text("UPDATE canvases SET version = 1 WHERE version IS NULL")
        )
        await conn.execute(
            text("ALTER TABLE templates ADD COLUMN IF NOT EXISTS creator_id VARCHAR(160)")
        )
        await conn.execute(
            text("ALTER TABLE templates ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1")
        )
        await conn.execute(
            text("UPDATE templates SET version = 1 WHERE version IS NULL")
        )
        await conn.execute(
            text("ALTER TABLE generation_runs ADD COLUMN IF NOT EXISTS owner_id VARCHAR(160)")
        )
