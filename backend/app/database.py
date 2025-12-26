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
        await conn.execute(
            text("ALTER TABLE video_segments ADD COLUMN IF NOT EXISTS work_id VARCHAR(120)")
        )
        await conn.execute(
            text("ALTER TABLE video_segments ADD COLUMN IF NOT EXISTS sequence_id VARCHAR(120)")
        )
        await conn.execute(
            text("ALTER TABLE video_segments ADD COLUMN IF NOT EXISTS scene_id VARCHAR(120)")
        )
        await conn.execute(
            text("ALTER TABLE video_segments ADD COLUMN IF NOT EXISTS shot_id VARCHAR(120)")
        )
        await conn.execute(
            text("ALTER TABLE source_packs ADD COLUMN IF NOT EXISTS source_snapshot_at TIMESTAMP")
        )
        await conn.execute(
            text("ALTER TABLE source_packs ADD COLUMN IF NOT EXISTS source_sync_at TIMESTAMP")
        )
        await conn.execute(
            text("ALTER TABLE source_packs ADD COLUMN IF NOT EXISTS source_count INTEGER DEFAULT 0")
        )
        await conn.execute(
            text("ALTER TABLE source_packs ADD COLUMN IF NOT EXISTS source_manifest JSONB DEFAULT '[]'::jsonb")
        )
        await conn.execute(
            text("UPDATE source_packs SET source_count = COALESCE(source_count, 0)")
        )
        await conn.execute(
            text("UPDATE source_packs SET source_manifest = '[]'::jsonb WHERE source_manifest IS NULL")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS notebook_id VARCHAR(64)")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS notebook_ref VARCHAR(400)")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS guide_type VARCHAR(32)")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS homage_guide TEXT")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS variation_guide TEXT")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS template_recommendations JSONB")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS user_fit_notes TEXT")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS persona_profile TEXT")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS synapse_logic TEXT")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS origin_notebook_id VARCHAR(64)")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS filter_notebook_id VARCHAR(64)")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS cluster_id VARCHAR(160)")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS cluster_label VARCHAR(200)")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS cluster_confidence FLOAT")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS source_pack_id VARCHAR(160)")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS story_beats JSONB DEFAULT '[]'::jsonb")
        )
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS storyboard_cards JSONB DEFAULT '[]'::jsonb")
        )
        await conn.execute(
            text("UPDATE evidence_records SET story_beats = '[]'::jsonb WHERE story_beats IS NULL")
        )
        await conn.execute(
            text("UPDATE evidence_records SET storyboard_cards = '[]'::jsonb WHERE storyboard_cards IS NULL")
        )
        await conn.execute(
            text("ALTER TABLE notebook_library ADD COLUMN IF NOT EXISTS cluster_id VARCHAR(160)")
        )
        await conn.execute(
            text("ALTER TABLE notebook_library ADD COLUMN IF NOT EXISTS cluster_label VARCHAR(200)")
        )
        await conn.execute(
            text("ALTER TABLE notebook_library ADD COLUMN IF NOT EXISTS cluster_tags JSONB")
        )
        await conn.execute(
            text("ALTER TABLE notebook_library ADD COLUMN IF NOT EXISTS owner_id VARCHAR(160)")
        )
        await conn.execute(
            text("ALTER TABLE notebook_library ADD COLUMN IF NOT EXISTS guide_scope VARCHAR(32)")
        )
        await conn.execute(
            text("ALTER TABLE notebook_library ADD COLUMN IF NOT EXISTS curator_notes TEXT")
        )
        await conn.execute(
            text("ALTER TABLE affiliate_referrals ADD COLUMN IF NOT EXISTS referee_verified_at TIMESTAMP")
        )
