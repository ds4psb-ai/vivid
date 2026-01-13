#!/usr/bin/env python3
"""RAG Quality Report Generator.

Runs evaluation cases and generates a structured JSON report.

Usage:
    python scripts/run_rag_quality_report.py
    python scripts/run_rag_quality_report.py --output data/reports/custom_report.json
    python scripts/run_rag_quality_report.py --no-llm  # Skip LLM-as-Judge
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Paths
EVAL_CASES_PATH = ROOT_DIR.parent / "data" / "rag_eval" / "rag_quality_cases.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR.parent / "data" / "reports"


def load_eval_cases() -> Dict[str, Any]:
    """Load evaluation cases from JSON file."""
    if EVAL_CASES_PATH.exists():
        with open(EVAL_CASES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cases": [], "thresholds": {}}


async def evaluate_single_case(
    case: Dict[str, Any],
    use_llm: bool = True,
) -> Dict[str, Any]:
    """Evaluate a single test case.
    
    Args:
        case: Test case with query, app_key, dimension, etc.
        use_llm: Whether to use LLM-as-Judge
    
    Returns:
        Evaluation result with scores
    """
    try:
        from app.rag.tier1_dimension_rag import get_dimension_rag
        
        dimension = case.get("dimension", "4D")
        rag = get_dimension_rag(dimension)
        
        if rag.client is None:
            return {
                "id": case.get("id"),
                "status": "skipped",
                "reason": "Qdrant unavailable",
            }
        
        # Search with dataset filter
        expected_datasets = case.get("expected_datasets", [])
        metadata_filters = {}
        if expected_datasets:
            metadata_filters["dataset_id"] = expected_datasets[0]
        
        results = rag.search(
            query=case.get("query", ""),
            limit=5,
            min_score=0.1,
            metadata_filters=metadata_filters if metadata_filters else None,
        )
        
        # Calculate metrics
        hit = len(results) > 0
        keyword_matches = 0
        expected_keywords = case.get("expected_keywords", [])
        
        for r in results:
            content = r.get("content", "").lower()
            for kw in expected_keywords:
                if kw.lower() in content:
                    keyword_matches += 1
        
        keyword_coverage = keyword_matches / len(expected_keywords) if expected_keywords else 1.0
        
        # Groundedness heuristic (evidence count based)
        groundedness = min(1.0, len(results) / 3)
        
        # Relevance heuristic (keyword overlap)
        relevance = keyword_coverage
        
        # LLM-as-Judge (optional)
        llm_groundedness = None
        llm_relevance = None
        
        if use_llm and os.environ.get("GEMINI_API_KEY") and results:
            from tests.e2e.test_rag_quality import evaluate_groundedness, evaluate_relevance
            
            combined_content = " ".join(r.get("content", "") for r in results)
            try:
                llm_groundedness = await evaluate_groundedness(
                    case.get("query", ""),
                    combined_content,
                    [r.get("content", "") for r in results],
                )
                llm_relevance = await evaluate_relevance(
                    case.get("query", ""),
                    combined_content,
                )
            except Exception as e:
                print(f"  ⚠️ LLM eval failed: {e}")
        
        # Deflection check
        deflection_correct = None
        if case.get("type") == "deflection":
            deflection_correct = len(results) < 2  # Should not find much
        
        return {
            "id": case.get("id"),
            "status": "passed" if hit else "failed",
            "query": case.get("query"),
            "type": case.get("type"),
            "hit": hit,
            "result_count": len(results),
            "groundedness_heuristic": groundedness,
            "relevance_heuristic": relevance,
            "llm_groundedness": llm_groundedness,
            "llm_relevance": llm_relevance,
            "keyword_coverage": keyword_coverage,
            "deflection_correct": deflection_correct,
        }
        
    except Exception as e:
        return {
            "id": case.get("id"),
            "status": "error",
            "error": str(e),
        }


async def run_quality_report(
    use_llm: bool = True,
) -> Dict[str, Any]:
    """Run all evaluation cases and generate report.
    
    Args:
        use_llm: Whether to use LLM-as-Judge
    
    Returns:
        Full quality report
    """
    eval_data = load_eval_cases()
    cases = eval_data.get("cases", [])
    thresholds = eval_data.get("thresholds", {})
    
    if not cases:
        return {"error": "No evaluation cases found"}
    
    print(f"📊 Running {len(cases)} evaluation cases...")
    
    results = []
    for i, case in enumerate(cases):
        print(f"  [{i+1}/{len(cases)}] {case.get('id')}: {case.get('query', '')[:40]}...")
        result = await evaluate_single_case(case, use_llm=use_llm)
        results.append(result)
    
    # Calculate summary stats
    passed = [r for r in results if r.get("status") == "passed"]
    failed = [r for r in results if r.get("status") == "failed"]
    skipped = [r for r in results if r.get("status") == "skipped"]
    errors = [r for r in results if r.get("status") == "error"]
    
    groundedness_scores = [r["groundedness_heuristic"] for r in results if "groundedness_heuristic" in r]
    relevance_scores = [r["relevance_heuristic"] for r in results if "relevance_heuristic" in r]
    
    avg_groundedness = sum(groundedness_scores) / len(groundedness_scores) if groundedness_scores else 0
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
    pass_rate = len(passed) / len(results) if results else 0
    
    # LLM scores if available
    llm_groundedness_scores = [r["llm_groundedness"] for r in results if r.get("llm_groundedness") is not None]
    llm_relevance_scores = [r["llm_relevance"] for r in results if r.get("llm_relevance") is not None]
    
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "version": eval_data.get("version", "1.0"),
        "summary": {
            "total_cases": len(cases),
            "passed": len(passed),
            "failed": len(failed),
            "skipped": len(skipped),
            "errors": len(errors),
            "pass_rate": pass_rate,
            "pass_threshold": thresholds.get("pass_rate", 0.7),
            "overall_passed": pass_rate >= thresholds.get("pass_rate", 0.7),
        },
        "metrics": {
            "avg_groundedness_heuristic": avg_groundedness,
            "avg_relevance_heuristic": avg_relevance,
            "avg_llm_groundedness": sum(llm_groundedness_scores) / len(llm_groundedness_scores) if llm_groundedness_scores else None,
            "avg_llm_relevance": sum(llm_relevance_scores) / len(llm_relevance_scores) if llm_relevance_scores else None,
            "min_groundedness_threshold": thresholds.get("min_groundedness", 0.6),
            "min_relevance_threshold": thresholds.get("min_relevance", 0.5),
        },
        "details": results,
    }
    
    return report


async def main():
    parser = argparse.ArgumentParser(description="Generate RAG Quality Report")
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: data/reports/rag_quality_YYYYMMDD.json)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM-as-Judge evaluations",
    )
    args = parser.parse_args()
    
    # Generate report
    report = await run_quality_report(use_llm=not args.no_llm)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = DEFAULT_OUTPUT_DIR / f"rag_quality_{date_str}.json"
    
    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"📊 RAG Quality Report Generated")
    print(f"{'='*50}")
    print(f"Output: {output_path}")
    print(f"Total: {report['summary']['total_cases']} cases")
    print(f"Passed: {report['summary']['passed']} ({report['summary']['pass_rate']:.1%})")
    print(f"Avg Groundedness: {report['metrics']['avg_groundedness_heuristic']:.2f}")
    print(f"Avg Relevance: {report['metrics']['avg_relevance_heuristic']:.2f}")
    print(f"Overall: {'✅ PASS' if report['summary']['overall_passed'] else '❌ FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
