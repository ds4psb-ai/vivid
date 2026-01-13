#!/usr/bin/env python3
"""
RAG Cache Tuning Report - Phase 2

Generate dimension-aware cache statistics for tuning.

Usage:
    python scripts/rag_cache_report.py --dry-run
    python scripts/rag_cache_report.py  # writes to data/reports/
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


async def generate_report(dry_run: bool = False) -> dict:
    """Generate cache tuning report by dimension."""
    from sqlalchemy import select, func, case, Integer
    
    # Lazy imports for standalone script
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    
    from app.database import get_db_context
    from app.models import RagSemanticCache
    
    async with get_db_context() as db:
        now = datetime.utcnow()
        
        # Query by dimension with CASE for stale count (DB-portable)
        stmt = select(
            RagSemanticCache.dimension,
            func.count(RagSemanticCache.id).label("total"),
            func.avg(RagSemanticCache.hit_count).label("avg_hits"),
            func.sum(
                case((RagSemanticCache.expires_at < now, 1), else_=0)
            ).label("stale_count"),
        ).group_by(RagSemanticCache.dimension)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        report = {
            "generated_at": now.isoformat(),
            "total_dimensions": len(rows),
            "by_dimension": [
                {
                    "dimension": row.dimension or "unknown",
                    "total_entries": row.total,
                    "avg_hit_count": round(float(row.avg_hits or 0), 2),
                    "stale_entries": row.stale_count or 0,
                    "stale_rate": round((row.stale_count or 0) / row.total * 100, 1)
                        if row.total > 0 else 0,
                }
                for row in rows
            ],
        }
        
        # Top 10 by hit_count - use id[:8] (hash prefix, no PII)
        top_stmt = select(
            RagSemanticCache.id,
            RagSemanticCache.dimension,
            RagSemanticCache.hit_count,
        ).order_by(RagSemanticCache.hit_count.desc()).limit(10)
        
        top_result = await db.execute(top_stmt)
        report["top_cached"] = [
            {"id_prefix": r.id[:8], "dimension": r.dimension, "hits": r.hit_count}
            for r in top_result.all()
        ]
        
        # Summary stats
        report["summary"] = {
            "total_entries": sum(d["total_entries"] for d in report["by_dimension"]),
            "total_stale": sum(d["stale_entries"] for d in report["by_dimension"]),
            "avg_stale_rate": round(
                sum(d["stale_rate"] for d in report["by_dimension"]) / len(report["by_dimension"])
                if report["by_dimension"] else 0,
                1
            ),
        }
        
    if not dry_run:
        # Write to repo root / data / reports
        report_dir = Path(__file__).resolve().parents[2] / "data" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"rag_cache_report_{datetime.now():%Y%m%d}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ Report written: {report_path}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate RAG cache tuning report")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout, don't save")
    args = parser.parse_args()
    asyncio.run(generate_report(args.dry_run))
