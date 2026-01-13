#!/usr/bin/env python3
"""
Cleanup old RouterDecisionLog entries - Phase 2

Usage:
    python scripts/cleanup_router_logs.py --days 7
    python scripts/cleanup_router_logs.py --days 14 --dry-run
"""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path


async def cleanup(days: int = 7, dry_run: bool = False) -> int:
    """Delete router decision logs older than N days."""
    from sqlalchemy import delete, select, func
    
    # Lazy imports
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    
    from app.database import get_db_context
    from app.models import RouterDecisionLog
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    async with get_db_context() as db:
        # Count first
        count_stmt = select(func.count(RouterDecisionLog.id)).where(
            RouterDecisionLog.created_at < cutoff
        )
        count_result = await db.execute(count_stmt)
        count = count_result.scalar() or 0
        
        if dry_run:
            print(f"🔍 Would delete {count} router logs older than {days} days")
            return count
        
        if count == 0:
            print(f"✅ No router logs older than {days} days to delete")
            return 0
        
        # Delete
        delete_stmt = delete(RouterDecisionLog).where(
            RouterDecisionLog.created_at < cutoff
        )
        result = await db.execute(delete_stmt)
        # commit handled by get_db_context()
        
        print(f"🗑️  Deleted {result.rowcount} router logs older than {days} days")
        return result.rowcount


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cleanup old router decision logs")
    parser.add_argument("--days", type=int, default=7, help="Delete logs older than N days")
    parser.add_argument("--dry-run", action="store_true", help="Count only, don't delete")
    args = parser.parse_args()
    asyncio.run(cleanup(args.days, args.dry_run))
