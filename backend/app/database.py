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
    """Initialize database connection.

    Note: Schema is managed by Alembic migrations, not create_all().
    In production, only verifies connection. In development, runs create_all()
    for convenience.

    Args:
        drop_all: If True, drop all tables first (dev only, dangerous!)
    """
    from app.config import settings
    import logging
    logger = logging.getLogger("database")

    # Import ALL models to register them with Base.metadata
    # This ensures create_all() knows about all tables
    try:
        import app.models  # noqa: F401
        import app.models_telemetry  # noqa: F401
        import app.models_feedback  # noqa: F401
        import app.models_uqsl  # noqa: F401
        import app.models_ip  # noqa: F401
        import app.models_workflow  # noqa: F401
        import app.models_ip_evidence  # noqa: F401
        import app.models_singularity  # noqa: F401
        import app.models_humancloud  # noqa: F401
        import app.models_settlement  # noqa: F401
        import app.models_sandbox  # noqa: F401
        import app.models_character  # noqa: F401
        import app.models_reference  # noqa: F401
        import app.models_review  # noqa: F401
        import app.models_marketplace  # noqa: F401
        import app.models_versioning  # noqa: F401
        import app.models_miniapps  # noqa: F401
        import app.models_analytics  # noqa: F401
        import app.models_dlq  # noqa: F401
        import app.models_constellation  # noqa: F401
        import app.models_ip_chat  # noqa: F401
        import app.models_mcp  # noqa: F401
        import app.models_tenant  # noqa: F401
        import app.models_outlier  # noqa: F401
        import app.models_personalization  # noqa: F401
        import app.models_outbox  # noqa: F401
        import app.models_logic_vector  # noqa: F401
        import app.models_pipeline  # noqa: F401
        import app.models_hitl  # noqa: F401
        logger.info(f"[DB] Registered {len(Base.metadata.tables)} tables with Base.metadata")
    except ImportError as e:
        logger.warning(f"[DB] Some models failed to import: {e}")

    async with engine.begin() as conn:
        # Verify connection works
        result = await conn.execute(text("SELECT 1"))
        logger.info("[DB] Database connection verified")

        # Development only: create_all for convenience
        if drop_all:
            await conn.run_sync(Base.metadata.drop_all)

        is_prod = settings.ENVIRONMENT.lower() in {"production", "prod", "staging"}

        if not is_prod:
            logger.info("[DB] Development mode - running create_all()")
            await conn.run_sync(Base.metadata.create_all)
        else:
            # Production: Create missing tables one by one
            # checkfirst=True only checks tables, not indexes
            # So we create each table individually and catch duplicate index errors
            logger.info("[DB] Production mode - creating missing tables individually")

            def create_tables_safely(sync_conn):
                from sqlalchemy import inspect
                from sqlalchemy.exc import ProgrammingError

                inspector = inspect(sync_conn)
                existing_tables = set(inspector.get_table_names())

                created = 0
                skipped = 0
                for table in Base.metadata.sorted_tables:
                    if table.name in existing_tables:
                        skipped += 1
                        continue
                    try:
                        table.create(sync_conn, checkfirst=True)
                        created += 1
                        logger.info(f"[DB] Created table: {table.name}")
                    except ProgrammingError as e:
                        if "already exists" in str(e):
                            skipped += 1
                        else:
                            logger.error(f"[DB] Failed to create {table.name}: {e}")
                            raise

                logger.info(f"[DB] Tables - created: {created}, skipped: {skipped}")

            await conn.run_sync(create_tables_safely)

