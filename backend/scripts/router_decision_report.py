#!/usr/bin/env python3
"""
RouterDecisionLog Analysis Report - Phase 3

Metrics from 2024/2026 RAG best practices:
- Strategy distribution by dimension
- Cache hit rate by dimension (NULL = unknown, treated as miss for rate calc)
- Router score distribution
- Feature usage (reranker/grounding)

Usage:
    python scripts/router_decision_report.py --days 7 --dry-run
    python scripts/router_decision_report.py --days 7
"""
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path


async def generate_report(days: int = 7, dry_run: bool = False) -> dict:
    """Generate router decision analysis report."""
    from sqlalchemy import select, func, case, or_
    
    # Lazy imports for standalone script
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    
    from app.database import get_db_context
    from app.models import RouterDecisionLog
    
    async with get_db_context() as db:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # 1. Strategy distribution by dimension
        strategy_stmt = select(
            RouterDecisionLog.dimension,
            RouterDecisionLog.strategy,
            func.count(RouterDecisionLog.id).label("count"),
        ).where(
            RouterDecisionLog.created_at >= cutoff
        ).group_by(RouterDecisionLog.dimension, RouterDecisionLog.strategy)
        
        strategy_result = await db.execute(strategy_stmt)
        strategy_data = [
            {"dimension": r.dimension or "unknown", "strategy": r.strategy, "count": r.count}
            for r in strategy_result.all()
        ]
        
        # 2. Cache hit rate by dimension
        # NULL cache_hit is treated as "unknown" (not counted as miss)
        # This is intentional - only explicit True/False are counted
        cache_stmt = select(
            RouterDecisionLog.dimension,
            func.sum(case((RouterDecisionLog.cache_hit == True, 1), else_=0)).label("hits"),
            func.sum(case((RouterDecisionLog.cache_hit == False, 1), else_=0)).label("misses"),
            func.sum(case(
                (RouterDecisionLog.cache_hit.is_(None), 1), else_=0
            )).label("unknown"),
            func.count(RouterDecisionLog.id).label("total"),
        ).where(
            RouterDecisionLog.created_at >= cutoff
        ).group_by(RouterDecisionLog.dimension)
        
        cache_result = await db.execute(cache_stmt)
        cache_data = []
        for r in cache_result.all():
            known_total = (r.hits or 0) + (r.misses or 0)
            cache_data.append({
                "dimension": r.dimension or "unknown",
                "hits": r.hits or 0,
                "misses": r.misses or 0,
                "unknown": r.unknown or 0,
                "total": r.total,
                # Hit rate based on known values only
                "hit_rate": round((r.hits or 0) / known_total * 100, 1) if known_total > 0 else None,
            })
        
        # 3. Router score distribution
        score_stmt = select(
            RouterDecisionLog.router_score,
            func.count(RouterDecisionLog.id).label("count"),
        ).where(
            RouterDecisionLog.created_at >= cutoff
        ).group_by(RouterDecisionLog.router_score).order_by(RouterDecisionLog.router_score)
        
        score_result = await db.execute(score_stmt)
        score_data = [
            {"score": r.router_score, "count": r.count}
            for r in score_result.all()
        ]
        
        # 4. Reranker/Grounding usage
        feature_stmt = select(
            func.sum(case((RouterDecisionLog.use_reranker == True, 1), else_=0)).label("reranker"),
            func.sum(case((RouterDecisionLog.use_grounding == True, 1), else_=0)).label("grounding"),
            func.count(RouterDecisionLog.id).label("total"),
        ).where(RouterDecisionLog.created_at >= cutoff)
        
        feature_result = await db.execute(feature_stmt)
        feature_row = feature_result.first()
        
        total_queries = feature_row.total or 0
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "total_queries": total_queries,
            "strategy_distribution": strategy_data,
            "cache_hit_by_dimension": cache_data,
            "score_distribution": score_data,
            "feature_usage": {
                "reranker_count": feature_row.reranker or 0,
                "grounding_count": feature_row.grounding or 0,
                "reranker_rate": round((feature_row.reranker or 0) / total_queries * 100, 1) if total_queries else 0,
                "grounding_rate": round((feature_row.grounding or 0) / total_queries * 100, 1) if total_queries else 0,
            },
            "recommendations": [],
        }
        
        # Generate recommendations based on best practices
        for dim in cache_data:
            if dim["hit_rate"] is not None and dim["hit_rate"] < 20:
                report["recommendations"].append({
                    "severity": "warning",
                    "dimension": dim["dimension"],
                    "issue": f"Low cache hit rate ({dim['hit_rate']}%)",
                    "action": "Consider TTL increase or similarity threshold adjustment (current: 0.92)",
                })
            if dim["unknown"] > dim["total"] * 0.5:
                report["recommendations"].append({
                    "severity": "info",
                    "dimension": dim["dimension"],
                    "issue": f"High unknown cache_hit ({dim['unknown']}/{dim['total']})",
                    "action": "Check if cache_hit is being set in hybrid_query",
                })
        
        # Check for strategy imbalance
        strategy_counts = {}
        for s in strategy_data:
            strategy_counts[s["strategy"]] = strategy_counts.get(s["strategy"], 0) + s["count"]
        
        if strategy_counts and total_queries > 0:
            for strategy, count in strategy_counts.items():
                pct = count / total_queries * 100
                if pct > 80:
                    report["recommendations"].append({
                        "severity": "warning",
                        "issue": f"Strategy imbalance: {strategy} is {pct:.0f}% of queries",
                        "action": "Review _determine_strategy thresholds in hybrid_rag.py",
                    })
    
    if not dry_run:
        report_dir = Path(__file__).resolve().parents[2] / "data" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"router_decision_report_{datetime.now():%Y%m%d}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ Report: {report_path}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate router decision analysis report")
    parser.add_argument("--days", type=int, default=7, help="Analysis period in days")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout only")
    args = parser.parse_args()
    asyncio.run(generate_report(args.days, args.dry_run))
