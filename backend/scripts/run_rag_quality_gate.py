#!/usr/bin/env python3
"""RAG Quality Gate.

Runs the quality report and fails the process when thresholds are not met.

Usage:
    python scripts/run_rag_quality_gate.py
    python scripts/run_rag_quality_gate.py --no-llm
    python scripts/run_rag_quality_gate.py --min-pass-rate 0.75
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_rag_quality_report import load_eval_cases, run_quality_report


def _resolve_thresholds(
    args: argparse.Namespace, eval_data: Dict[str, Any]
) -> Tuple[float, float, float]:
    thresholds = eval_data.get("thresholds", {})
    pass_rate = args.min_pass_rate or thresholds.get("pass_rate", 0.7)
    groundedness = args.min_groundedness or thresholds.get("min_groundedness", 0.6)
    relevance = args.min_relevance or thresholds.get("min_relevance", 0.5)
    return pass_rate, groundedness, relevance


def _pick_metric(metrics: Dict[str, Any], llm_key: str, heuristic_key: str) -> float:
    value = metrics.get(llm_key)
    if value is None:
        return float(metrics.get(heuristic_key, 0))
    return float(value)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG Quality Gate")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM-as-judge scoring.")
    parser.add_argument("--min-pass-rate", type=float, help="Override pass rate threshold.")
    parser.add_argument("--min-groundedness", type=float, help="Override groundedness threshold.")
    parser.add_argument("--min-relevance", type=float, help="Override relevance threshold.")
    parser.add_argument(
        "--allow-skipped",
        action="store_true",
        help="Allow skipped cases without failing the gate.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Optional report output path (default: data/reports/rag_quality_gate_YYYYMMDD.json)",
    )
    args = parser.parse_args()

    eval_data = load_eval_cases()
    pass_rate_threshold, groundedness_threshold, relevance_threshold = _resolve_thresholds(
        args, eval_data
    )

    report = await run_quality_report(use_llm=not args.no_llm)
    metrics = report.get("metrics", {})
    summary = report.get("summary", {})

    pass_rate = float(summary.get("pass_rate", 0))
    avg_groundedness = _pick_metric(metrics, "avg_llm_groundedness", "avg_groundedness_heuristic")
    avg_relevance = _pick_metric(metrics, "avg_llm_relevance", "avg_relevance_heuristic")

    deflection_failures = [
        case for case in report.get("details", [])
        if case.get("type") == "deflection" and case.get("deflection_correct") is False
    ]

    failed_reasons = []
    if pass_rate < pass_rate_threshold:
        failed_reasons.append(f"pass_rate {pass_rate:.2f} < {pass_rate_threshold:.2f}")
    if avg_groundedness < groundedness_threshold:
        failed_reasons.append(
            f"groundedness {avg_groundedness:.2f} < {groundedness_threshold:.2f}"
        )
    if avg_relevance < relevance_threshold:
        failed_reasons.append(
            f"relevance {avg_relevance:.2f} < {relevance_threshold:.2f}"
        )
    if deflection_failures:
        failed_reasons.append("deflection cases failed")
    if summary.get("errors"):
        failed_reasons.append("errors in evaluation cases")
    if summary.get("skipped") and not args.allow_skipped:
        failed_reasons.append("skipped cases detected")

    # Persist report if requested (or default)
    output_path: Path
    if args.output:
        output_path = Path(args.output)
    else:
        reports_dir = ROOT_DIR.parent / "data" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = reports_dir / f"rag_quality_gate_{date_str}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print("\n" + "=" * 56)
    print("🧪 RAG Quality Gate")
    print("=" * 56)
    print(f"Pass rate: {pass_rate:.2%} (threshold {pass_rate_threshold:.2%})")
    print(f"Groundedness: {avg_groundedness:.2f} (threshold {groundedness_threshold:.2f})")
    print(f"Relevance: {avg_relevance:.2f} (threshold {relevance_threshold:.2f})")
    print(f"Deflection failures: {len(deflection_failures)}")
    print(f"Report saved: {output_path}")

    if failed_reasons:
        print("❌ QUALITY GATE FAILED")
        for reason in failed_reasons:
            print(f" - {reason}")
        raise SystemExit(2)

    print("✅ QUALITY GATE PASSED")


if __name__ == "__main__":
    asyncio.run(main())
