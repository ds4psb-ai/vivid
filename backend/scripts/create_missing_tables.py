#!/usr/bin/env python3
"""Create all missing database tables using SQLAlchemy.

This script imports all models and creates tables one by one,
handling duplicate index errors gracefully.

Usage:
    DATABASE_URL=... python scripts/create_missing_tables.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import ProgrammingError

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

    # First, drop orphaned indexes (indexes for tables that don't exist)
    print("[INFO] Checking for orphaned indexes...")
    with engine.begin() as conn:
        # Find all indexes that reference non-existent tables
        result = conn.execute(text("""
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename NOT IN (
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            )
        """))
        orphaned = result.fetchall()

        for idx_name, table_name in orphaned:
            try:
                conn.execute(text(f'DROP INDEX IF EXISTS "{idx_name}"'))
                print(f"[OK] Dropped orphaned index: {idx_name}")
            except Exception as e:
                print(f"[WARN] Could not drop {idx_name}: {e}")

    # Get existing tables
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    print(f"[INFO] Tables before: {len(existing_tables)}")

    # Get all tables defined in models
    model_tables = set(Base.metadata.tables.keys())
    print(f"[INFO] Tables defined in models: {len(model_tables)}")

    # Find missing tables
    missing_tables = model_tables - existing_tables
    print(f"[INFO] Missing tables: {len(missing_tables)}")

    if not missing_tables:
        print("[INFO] All tables already exist. Nothing to do.")
        return

    print(f"[INFO] Creating {len(missing_tables)} missing tables...")

    created = 0
    skipped = 0
    errors = 0

    # Create tables one by one to handle errors gracefully
    for table_name in sorted(missing_tables):
        table = Base.metadata.tables.get(table_name)
        if table is None:
            continue

        try:
            # Use a fresh connection for each table to avoid transaction issues
            with engine.begin() as conn:
                table.create(conn, checkfirst=True)
            created += 1
            print(f"[OK] Created: {table_name}")
        except ProgrammingError as e:
            error_msg = str(e)
            if "already exists" in error_msg:
                skipped += 1
                # Extract what already exists (table or index)
                if "relation" in error_msg:
                    print(f"[SKIP] {table_name} (index already exists)")
                else:
                    print(f"[SKIP] {table_name} (already exists)")
            else:
                errors += 1
                print(f"[ERROR] {table_name}: {e}")
        except Exception as e:
            errors += 1
            print(f"[ERROR] {table_name}: {e}")

    print(f"\n[SUMMARY] Created: {created}, Skipped: {skipped}, Errors: {errors}")

    # Verify final state
    inspector = inspect(engine)
    final_tables = set(inspector.get_table_names())
    print(f"[INFO] Tables after: {len(final_tables)}")

    still_missing = model_tables - final_tables
    if still_missing:
        print(f"[WARNING] Still missing {len(still_missing)} tables")
    else:
        print("[SUCCESS] All model tables now exist!")


if __name__ == "__main__":
    main()
