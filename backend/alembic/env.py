"""Alembic env.py - Configured for sync SQLAlchemy with Vivid models.

Note: Alembic migrations run with SYNC driver (psycopg2), not async (asyncpg).
The app uses asyncpg at runtime, but migrations use psycopg2 for compatibility.
"""
from logging.config import fileConfig

from sqlalchemy import pool, create_engine

from alembic import context

# Import all models for autogenerate support
from app.database import Base
from app.models import *  # noqa: F401, F403
from app.models_telemetry import *  # noqa: F401, F403
from app.models_feedback import *  # noqa: F401, F403  # P6: RAG Feedback
from app.models_uqsl import *  # noqa: F401, F403  # UQSL: Quality Selection Layer
from app.models_ip import *  # noqa: F401, F403  # IP-First UX models
from app.models_workflow import *  # noqa: F401, F403  # Workflow Checkpoint models
from app.models_ip_evidence import *  # noqa: F401, F403  # IP Evidence models
# Additional models that must be imported for complete schema
from app.models_singularity import *  # noqa: F401, F403  # Blackhole templates
from app.models_humancloud import *  # noqa: F401, F403  # Human Cloud
from app.models_settlement import *  # noqa: F401, F403  # Settlement
from app.models_sandbox import *  # noqa: F401, F403  # Sandbox
from app.models_character import *  # noqa: F401, F403  # Character consistency
from app.models_reference import *  # noqa: F401, F403  # Reference decoder
from app.models_review import *  # noqa: F401, F403  # Review
from app.models_marketplace import *  # noqa: F401, F403  # Marketplace
from app.models_versioning import *  # noqa: F401, F403  # Versioning
from app.models_miniapps import *  # noqa: F401, F403  # Miniapps
from app.models_analytics import *  # noqa: F401, F403  # Analytics
from app.models_dlq import *  # noqa: F401, F403  # DLQ
from app.models_constellation import *  # noqa: F401, F403  # Constellation
from app.models_ip_chat import *  # noqa: F401, F403  # IP Chat
from app.models_tenant import *  # noqa: F401, F403  # Tenant
from app.models_outlier import *  # noqa: F401, F403  # Outlier
from app.models_personalization import *  # noqa: F401, F403  # Personalization
from app.models_outbox import *  # noqa: F401, F403  # Outbox
from app.models_logic_vector import *  # noqa: F401, F403  # Logic vector
from app.models_pipeline import *  # noqa: F401, F403  # Pipeline
from app.models_hitl import *  # noqa: F401, F403  # HITL
from app.models_rights_graph import *  # noqa: F401, F403  # Rights graph

# Load settings
from app.config import settings

# this is the Alembic Config object
config = context.config

# Set the database URL from settings
# Convert async driver (+asyncpg) to sync driver (+psycopg2) for Alembic
sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with sync engine.

    Uses psycopg2 (sync) driver instead of asyncpg for Alembic compatibility.
    """
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
