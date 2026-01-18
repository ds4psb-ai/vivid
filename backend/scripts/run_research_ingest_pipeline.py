#!/usr/bin/env python3
"""One-shot pipeline: Tavily research → ingest → quality gate.

Usage:
    # Use preset queries + metadata for a dimension
    python scripts/run_research_ingest_pipeline.py --preset 4D

    # Custom queries + metadata overrides
    python scripts/run_research_ingest_pipeline.py \
      --dimension 4D \
      --query "film analysis framework" \
      --query "cinematography analysis methods" \
      --dataset-id film_analysis \
      --app-key teaching.reference.analyze

    # Skip indexing but save research outputs
    python scripts/run_research_ingest_pipeline.py --preset 1D --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add backend to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from app.rag.research_pipeline import ResearchPipeline
from ingest_research_corpus import ingest_documents
from run_rag_quality_report import load_eval_cases, run_quality_report


DIMENSION_PRESETS: Dict[str, Dict[str, Any]] = {
    "1D": {
        "dimension": "1D",
        "app_key": "dimension.1d.prompt",
        "queries": [
            "video generation prompt engineering",
            "text to video prompt best practices",
            "VEO prompt guide",
            "Runway Gen-3 prompting",
            "Sora prompt guide",
        ],
    },
    "PROMPT": {
        "dimension": "1D",
        "app_key": "dimension.1d.prompt",
        "queries": [
            "video generation prompt engineering",
            "text to video prompt best practices",
            "VEO prompt guide",
            "Runway Gen-3 prompting",
            "Sora prompt guide",
        ],
    },
    "2D": {
        "dimension": "2D",
        "app_key": "dimension.story.architect",
        "queries": [
            "storyboard narrative structure",
            "story beat mapping",
            "screenplay scene breakdown",
            "hero's journey beat sheet",
            "save the cat beat sheet",
        ],
    },
    "STORY": {
        "dimension": "2D",
        "app_key": "dimension.story.architect",
        "dataset_id": "story_templates",
        "queries": [
            "storyboard narrative structure",
            "story beat mapping",
            "screenplay scene breakdown",
            "hero's journey beat sheet",
            "save the cat beat sheet",
        ],
    },
    "STORYBOARD": {
        "dimension": "2D",
        "app_key": "teaching.storyboard.create",
        "dataset_id": "storyboard_composition_rules",
        "queries": [
            "storyboard panel composition rules",
            "shot list storyboard template",
            "camera movement notation storyboard",
            "storyboard character consistency techniques",
        ],
    },
    "3D": {
        "dimension": "3D",
        "app_key": "dimension.3d.image",
        "queries": [
            "cinematography composition framing",
            "lighting techniques film",
            "color grading film theory",
            "shot composition analysis",
        ],
    },
    "IMAGE": {
        "dimension": "3D",
        "app_key": "dimension.3d.image",
        "queries": [
            "cinematography composition framing",
            "lighting techniques film",
            "color grading film theory",
            "shot composition analysis",
        ],
    },
    "4D": {
        "dimension": "4D",
        "app_key": "teaching.reference.analyze",
        "dataset_id": "film_analysis",
        "queries": [
            "film analysis framework",
            "cinematography analysis methods",
            "visual language film theory",
            "mise en scene analysis",
        ],
    },
    "5D": {
        "dimension": "5D",
        "app_key": "veo.video.generate",
        "queries": [
            "camera movement techniques film",
            "video transition effects",
            "visual rhythm editing techniques",
            "VEO camera movement guide",
        ],
    },
    "VEO": {
        "dimension": "5D",
        "app_key": "veo.video.generate",
        "queries": [
            "camera movement techniques film",
            "video transition effects",
            "visual rhythm editing techniques",
            "VEO camera movement guide",
        ],
    },
    "6D": {
        "dimension": "6D",
        "app_key": "dimension.6d.sound",
        "queries": [
            "film sound design principles",
            "diegetic non-diegetic sound",
            "cinematic soundscape techniques",
            "film score composition",
        ],
    },
    "AD": {
        "dimension": "AD",
        "app_key": "dimension.aesthetic.direct",
        "queries": [
            "aesthetic film theory",
            "visual style analysis",
            "color grading philosophy",
            "director visual style analysis",
        ],
    },
    "QC": {
        "dimension": "QC",
        "app_key": "dimension.quality.check",
        "queries": [
            "video quality assessment vmaf",
            "perceptual video quality metrics",
            "ssim lpips fid quality metrics",
        ],
    },
    # Research-only presets (RAG ingest disabled)
    "MIRROR": {
        "dimension": "AI",
        "app_key": "mirror.persona.analyze",
        "skip_ingest": True,
        "skip_quality_gate": True,
        "save_output": True,
        "queries": [
            "big five personality traits markers",
            "attachment theory adult styles",
            "jungian archetypes creativity",
            "mbti creativity correlations",
        ],
    },
    "CHARACTER": {
        "dimension": "CHARACTER",
        "app_key": "dimension.character.manage",
        "skip_ingest": True,
        "skip_quality_gate": True,
        "save_output": True,
        "queries": [
            "character consistency storyboard techniques",
            "multi-shot character reference design",
            "character sheet visual guide",
            "storymem character consistency paper",
        ],
    },
}


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


async def _run_quality_gate(
    *,
    use_llm: bool,
    min_pass_rate: Optional[float],
    min_groundedness: Optional[float],
    min_relevance: Optional[float],
    allow_skipped: bool,
    output_path: Optional[Path],
) -> bool:
    eval_data = load_eval_cases()
    pass_rate_threshold, groundedness_threshold, relevance_threshold = _resolve_thresholds(
        argparse.Namespace(
            min_pass_rate=min_pass_rate,
            min_groundedness=min_groundedness,
            min_relevance=min_relevance,
        ),
        eval_data,
    )

    report = await run_quality_report(use_llm=use_llm)
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
    if summary.get("skipped") and not allow_skipped:
        failed_reasons.append("skipped cases detected")

    if output_path is None:
        reports_dir = ROOT_DIR.parent / "data" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = reports_dir / f"rag_quality_pipeline_{date_str}.json"

    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print("\n" + "=" * 56)
    print("🧪 RAG Quality Gate (pipeline)")
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
        return False

    print("✅ QUALITY GATE PASSED")
    return True


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run research → ingest → quality gate pipeline.")
    parser.add_argument("--preset", choices=sorted(DIMENSION_PRESETS.keys()), help="Preset to run.")
    parser.add_argument("--dimension", help="Override dimension (1D,2D,3D,4D,5D,6D,AD,QC).")
    parser.add_argument("--query", action="append", help="Custom query (repeatable).")
    parser.add_argument("--max-results", type=int, default=8, help="Max results per query.")
    parser.add_argument("--search-depth", default="advanced", choices=["basic", "advanced"])
    parser.add_argument("--include-domain", action="append", help="Limit search to domains.")
    parser.add_argument("--exclude-domain", action="append", help="Exclude domains.")
    parser.add_argument("--dataset-id", help="dataset_id metadata override.")
    parser.add_argument("--app-key", help="app_key metadata override.")
    parser.add_argument("--min-score", type=float, default=0.55, help="Min relevance score.")
    parser.add_argument("--min-quality", default="standard", choices=["low", "standard", "high"])
    parser.add_argument("--allow-license", default="permissive,unknown")
    parser.add_argument("--min-content-len", type=int, default=200)
    parser.add_argument("--extract-mode", default="auto", choices=["auto", "force", "off"])
    parser.add_argument("--dry-run", action="store_true", help="Skip indexing.")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip ingest entirely.")
    parser.add_argument("--save-output", action="store_true", help="Save research output JSON.")
    parser.add_argument("--output", help="Output JSON file for research docs.")
    parser.add_argument("--skip-quality-gate", action="store_true")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM-as-judge scoring.")
    parser.add_argument("--min-pass-rate", type=float)
    parser.add_argument("--min-groundedness", type=float)
    parser.add_argument("--min-relevance", type=float)
    parser.add_argument("--allow-skipped", action="store_true")
    args = parser.parse_args()

    preset = DIMENSION_PRESETS.get(args.preset) if args.preset else {}
    dimension = (args.dimension or preset.get("dimension"))
    if not dimension:
        raise SystemExit("Provide --preset or --dimension.")
    dimension = dimension.upper()

    queries = args.query or preset.get("queries") or []
    if not queries:
        raise SystemExit("No queries provided. Use --query or --preset.")

    dataset_id = args.dataset_id or preset.get("dataset_id")
    app_key = args.app_key or preset.get("app_key")
    skip_ingest = args.skip_ingest or preset.get("skip_ingest", False)
    skip_quality_gate = args.skip_quality_gate or preset.get("skip_quality_gate", False)
    save_output = args.save_output or preset.get("save_output", False)

    pipeline = ResearchPipeline()
    all_docs: List[Dict[str, Any]] = []

    for query in queries:
        result = await pipeline.research(
            query=query,
            dimension=dimension,
            max_results=args.max_results,
            search_depth=args.search_depth,
            include_domains=args.include_domain,
            exclude_domains=args.exclude_domain,
            extract_mode=args.extract_mode,
            allow_unknown_license=True,
            save_results=False,
        )
        all_docs.extend([doc.to_dict() for doc in result.documents])

    output_path = None
    if save_output or args.output:
        if args.output:
            output_path = Path(args.output)
        else:
            out_dir = ROOT_DIR.parent / "data" / "source_packs" / "research"
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = out_dir / f"research_{dimension.lower()}_{ts}.json"
        output_path.write_text(json.dumps(all_docs, ensure_ascii=False, indent=2))
        print(f"Saved research output: {output_path}")

    if skip_ingest:
        print("[SKIP] Ingest disabled for this preset.")
        if not skip_quality_gate:
            print("[SKIP] Quality gate disabled because ingest is skipped.")
            skip_quality_gate = True
    else:
        allow_license = {item.strip().lower() for item in args.allow_license.split(",") if item.strip()}
        stats = ingest_documents(
            all_docs,
            dimension_override=dimension,
            dataset_id=dataset_id,
            app_key=app_key,
            min_score=args.min_score,
            min_quality=args.min_quality,
            allowed_licenses=allow_license,
            min_content_len=args.min_content_len,
            dry_run=args.dry_run,
        )

        print(
            f"[{'DRY RUN' if args.dry_run else 'INDEX'}] "
            f"Loaded: {stats['loaded']} | Eligible: {stats['eligible']} | Indexed: {stats['indexed']}"
        )
        print(f"Skipped: {stats['skipped']}")

    if skip_quality_gate:
        return

    ok = await _run_quality_gate(
        use_llm=not args.no_llm,
        min_pass_rate=args.min_pass_rate,
        min_groundedness=args.min_groundedness,
        min_relevance=args.min_relevance,
        allow_skipped=args.allow_skipped,
        output_path=None,
    )
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    asyncio.run(main())
