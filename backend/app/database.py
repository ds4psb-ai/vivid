"""
Database setup (async SQLAlchemy + asyncpg)

Security Note (H1.4b):
- Includes RLS context support via ContextVar
- Use get_db_with_rls() for tenant-isolated queries
- TenantMiddleware sets the current_tenant ContextVar

Security Note (H2.2):
- SSL connection is configurable via DB_SSL_MODE setting
- Production should use "require" or "verify-full"
"""
import ssl
from contextvars import ContextVar
from typing import Optional, AsyncGenerator, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# H1.4b: ContextVar for current tenant (set by TenantMiddleware)
current_tenant: ContextVar[Optional[str]] = ContextVar("current_tenant", default=None)


def _build_ssl_context() -> Any:
    """Build SSL context based on DB_SSL_MODE setting.

    H2.2: Database SSL Security
    - disable: No SSL
    - allow/prefer: SSL optional (development)
    - require: SSL mandatory (production baseline)
    - verify-ca/verify-full: SSL + certificate verification (highest security)
    """
    ssl_mode = settings.DB_SSL_MODE.lower()

    if ssl_mode == "disable":
        return None

    if ssl_mode in {"allow", "prefer"}:
        # SSL optional - asyncpg handles this mode
        return ssl_mode

    if ssl_mode == "require":
        # SSL required but no cert verification
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    if ssl_mode in {"verify-ca", "verify-full"}:
        # SSL with certificate verification
        ctx = ssl.create_default_context()
        if ssl_mode == "verify-full":
            ctx.check_hostname = True
        else:
            ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    # Default to prefer for unknown modes
    return "prefer"


# H2.2: Build connect_args with SSL configuration
_connect_args: dict[str, Any] = {}
_ssl_context = _build_ssl_context()
if _ssl_context is not None:
    _connect_args["ssl"] = _ssl_context


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.ENVIRONMENT == "development",
    # Performance tuning: connection pool configuration
    pool_size=10,           # Maintain 10 persistent connections
    max_overflow=20,        # Allow up to 20 extra connections during peak
    pool_recycle=1800,      # Recycle connections after 30 minutes (prevent stale)
    pool_timeout=30,        # Wait max 30s for available connection
    # H2.2: SSL connection configuration
    connect_args=_connect_args,
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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session without RLS context.

    Use this for system operations or when tenant context is not needed.
    For tenant-isolated queries, use get_db_with_rls() instead.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_with_rls() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with RLS context for tenant isolation.

    H1.4b Security Enhancement:
    - Sets app.current_tenant session variable from ContextVar
    - Enables PostgreSQL Row Level Security enforcement
    - Tenant data is automatically filtered at database level

    Usage:
        @router.get("/data")
        async def get_data(
            db: AsyncSession = Depends(get_db_with_rls),
            tenant: Tenant = Depends(require_tenant),
        ):
            # Query automatically filtered by tenant
            result = await db.execute(select(CapsuleRun))
            return result.scalars().all()

    Note:
        SET LOCAL is used, so the setting is transaction-scoped
        and automatically cleared when the session ends.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get tenant from ContextVar (set by TenantMiddleware)
            tenant_id = current_tenant.get()

            if tenant_id:
                # Set PostgreSQL session variable for RLS
                # Using SET LOCAL so it's transaction-scoped
                await session.execute(
                    text("SET LOCAL app.current_tenant = :tenant_id"),
                    {"tenant_id": tenant_id}
                )

            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_context():
    """Async context manager for database sessions (for use outside FastAPI Depends).
    
    Usage:
        async with get_db_context() as db:
            result = await db.execute(...)
    
    Note:
        - Always commits on success, rolls back on exception
        - Session is properly closed even if exception occurs
    """
    session = AsyncSessionLocal()
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
        # Gap 1: persona_source for EvidenceRecord
        await conn.execute(
            text("ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS persona_source VARCHAR(32)")
        )
        # Gap 2: segment_type for VideoSegment
        await conn.execute(
            text("ALTER TABLE video_segments ADD COLUMN IF NOT EXISTS segment_type VARCHAR(32)")
        )
        # Gap 3 & 4: persona_priority and persona_source for CapsuleRun
        await conn.execute(
            text("ALTER TABLE capsule_runs ADD COLUMN IF NOT EXISTS persona_priority VARCHAR(32)")
        )
        await conn.execute(
            text("ALTER TABLE capsule_runs ADD COLUMN IF NOT EXISTS persona_source VARCHAR(32)")
        )
        # Analytics events table (Phase 0.1)
        await conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    event_type VARCHAR(60) NOT NULL,
                    user_id VARCHAR(160),
                    template_id UUID,
                    capsule_id VARCHAR(160),
                    run_id UUID,
                    evidence_ref VARCHAR(200),
                    meta JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        # Index for analytics queries
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_analytics_events_created ON analytics_events(created_at)")
        )

        # RAG Semantic Cache with pgvector (Week 2.5)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        await conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS rag_semantic_cache (
                    id VARCHAR(64) PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    embedding vector(768),
                    response_json JSONB DEFAULT '{}'::jsonb,
                    auteur_key VARCHAR(64),
                    dimension VARCHAR(16),
                    hit_count INTEGER DEFAULT 0,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_rag_cache_created ON rag_semantic_cache(created_at)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_rag_cache_expires ON rag_semantic_cache(expires_at)")
        )
        # HNSW index for fast vector search (requires pgvector 0.5.0+)
        try:
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_rag_cache_embedding ON rag_semantic_cache USING hnsw (embedding vector_cosine_ops)")
            )
        except Exception:
            # Fallback for older pgvector or if index creation fails
            pass

        # Studio Artifacts storage (Week 2.5)
        await conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS studio_artifacts (
                    id VARCHAR(64) PRIMARY KEY,
                    artifact_type VARCHAR(32) NOT NULL,
                    auteur_key VARCHAR(64),
                    focus_topic TEXT NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    storage_path VARCHAR(500) NOT NULL,
                    storage_url VARCHAR(500),
                    file_size_bytes INTEGER DEFAULT 0,
                    mime_type VARCHAR(100),
                    notebook_id VARCHAR(64),
                    source_ids JSONB DEFAULT '[]'::jsonb,
                    generation_params JSONB DEFAULT '{}'::jsonb,
                    access_count INTEGER DEFAULT 0,
                    last_accessed_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_artifacts_key ON studio_artifacts(auteur_key, artifact_type)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_artifacts_expires ON studio_artifacts(expires_at)")
        )

