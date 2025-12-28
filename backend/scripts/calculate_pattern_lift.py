#!/usr/bin/env python3
"""Calculate and display Pattern Lift report.

Usage:
    python backend/scripts/calculate_pattern_lift.py
    python backend/scripts/calculate_pattern_lift.py --min-sample 5 --output json

Reference: 07_EXECUTION_PLAN_2025-12.md Phase 2.1
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pattern_lift import calculate_pattern_lift_report, get_top_patterns_by_lift


def format_lift(lift_pct: float) -> str:
    """Format lift percentage with color indicator."""
    if lift_pct > 0:
        return f"+{lift_pct:.1f}%"
    elif lift_pct < 0:
        return f"{lift_pct:.1f}%"
    return "0.0%"


async def main():
    parser = argparse.ArgumentParser(description="Calculate Pattern Lift Report")
    parser.add_argument(
        "--min-sample",
        type=int,
        default=3,
        help="Minimum sample size for valid lift calculation (default: 3)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum patterns to display (default: 20)",
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--min-lift",
        type=float,
        default=None,
        help="Minimum lift threshold to include",
    )
    args = parser.parse_args()

    print(f"[{datetime.now().isoformat()}] Calculating Pattern Lift Report...")
    print(f"  Min sample size: {args.min_sample}")
    print()

    results = await calculate_pattern_lift_report(min_sample_size=args.min_sample)

    if args.min_lift is not None:
        results = [r for r in results if r.lift >= args.min_lift]

    results = results[: args.limit]

    if not results:
        print("No patterns found with sufficient sample size.")
        return

    if args.output == "json":
        output_data = [
            {
                "pattern_id": r.pattern_id,
                "pattern_name": r.pattern_name,
                "pattern_type": r.pattern_type,
                "parent_metric": r.parent_metric,
                "variant_metric": r.variant_metric,
                "lift": r.lift,
                "lift_pct": r.lift_pct,
                "sample_size": r.sample_size,
                "calculated_at": r.calculated_at.isoformat(),
            }
            for r in results
        ]
        print(json.dumps(output_data, indent=2))
    else:
        # Table format
        print(f"{'Pattern Name':<40} {'Type':<12} {'Lift':<12} {'Samples':<8} {'Parent':<10} {'Variant':<10}")
        print("-" * 92)
        for r in results:
            lift_str = format_lift(r.lift_pct)
            print(
                f"{r.pattern_name[:38]:<40} "
                f"{r.pattern_type:<12} "
                f"{lift_str:<12} "
                f"{r.sample_size:<8} "
                f"{r.parent_metric:.3f}     "
                f"{r.variant_metric:.3f}"
            )
        print("-" * 92)
        print(f"Total patterns: {len(results)}")

    # Summary stats
    if results:
        avg_lift = sum(r.lift_pct for r in results) / len(results)
        max_lift = max(r.lift_pct for r in results)
        min_lift = min(r.lift_pct for r in results)
        print()
        print(f"Summary: Avg Lift={avg_lift:.1f}%, Max={max_lift:.1f}%, Min={min_lift:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
