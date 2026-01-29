#!/usr/bin/env python3
"""Create all missing database tables using SQLAlchemy create_all().

This script imports all models and runs Base.metadata.create_all()
to create any tables that don't exist yet.

Usage:
    DATABASE_URL=... python scripts/create_missing_tables.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

# Import Base first
from app.database import Base

# Import ALL models to register them with Base.metadata
from app.models import *  # noqa: F401, F403
from app.models_telemetry import *  # noqa: F401, F403
from app.models_feedback import *  # noqa: F401, F403
from app.models_uqsl import *  # noqa: F401, F403
from app.models_ip import *  # noqa: F401, F403
from app.models_workflow import *  # noqa: F401, F403
from app.models_ip_evidence import *  # noqa: F401, F403
from app.models_singularity import *  # noqa: F401, F403
from app.models_humancloud import *  # noqa: F401, F403
from app.models_settlement import *  # noqa: F401, F403
from app.models_sandbox import *  # noqa: F401, F403
from app.models_character import *  # noqa: F401, F403
from app.models_reference import *  # noqa: F401, F403
from app.models_review import *  # noqa: F401, F403
from app.models_marketplace import *  # noqa: F401, F403
from app.models_versioning import *  # noqa: F401, F403
from app.models_miniapps import *  # noqa: F401, F403
from app.models_analytics import *  # noqa: F401, F403
from app.models_dlq import *  # noqa: F401, F403
from app.models_constellation import *  # noqa: F401, F403
from app.models_ip_chat import *  # noqa: F401, F403
from app.models_mcp import *  # noqa: F401, F403
from app.models_tenant import *  # noqa: F401, F403
from app.models_outlier import *  # noqa: F401, F403
from app.models_personalization import *  # noqa: F401, F403
from app.models_outbox import *  # noqa: F401, F403
from app.models_logic_vector import *  # noqa: F401, F403
from app.models_pipeline import *  # noqa: F401, F403
from app.models_hitl import *  # noqa: F401, F403

from app.config import settings


def main():
    # Convert async URL to sync URL for this script
    db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
    sync_url = db_url.replace("+asyncpg", "+psycopg2")

    print(f"[INFO] Connecting to database...")
    engine = create_engine(sync_url)

    with engine.connect() as conn:
        # Count tables before
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        before_count = result.scalar()
        print(f"[INFO] Tables before: {before_count}")

        # List existing tables
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        ))
        existing_tables = [row[0] for row in result.fetchall()]
        print(f"[INFO] Existing tables: {existing_tables}")

    # Get all tables defined in models
    model_tables = set(Base.metadata.tables.keys())
    print(f"[INFO] Tables defined in models: {len(model_tables)}")

    # Find missing tables
    missing_tables = model_tables - set(existing_tables)
    print(f"[INFO] Missing tables: {sorted(missing_tables)}")

    if not missing_tables:
        print("[INFO] All tables already exist. Nothing to do.")
        return

    print(f"[INFO] Creating {len(missing_tables)} missing tables...")

    # Create all tables (checkfirst=True means it won't fail if table exists)
    Base.metadata.create_all(engine, checkfirst=True)

    with engine.connect() as conn:
        # Count tables after
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        after_count = result.scalar()
        print(f"[INFO] Tables after: {after_count}")
        print(f"[INFO] Created {after_count - before_count} new tables")

        # Verify missing tables are now created
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        ))
        new_tables = [row[0] for row in result.fetchall()]

        still_missing = model_tables - set(new_tables)
        if still_missing:
            print(f"[WARNING] Still missing tables: {sorted(still_missing)}")
        else:
            print("[SUCCESS] All model tables now exist!")


if __name__ == "__main__":
    main()
