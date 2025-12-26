import argparse
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.pattern_promotion import DEFAULT_MIN_CONFIDENCE, run_pattern_promotion


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote validated pattern candidates into Pattern Library."
    )
    parser.add_argument(
        "--derive-from-evidence",
        action="store_true",
        help="Create proposed candidates from evidence key_patterns.",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=DEFAULT_MIN_CONFIDENCE,
        help="Min confidence for validated.",
    )
    parser.add_argument(
        "--min-sources",
        type=int,
        default=2,
        help="Min distinct sources for promotion.",
    )
    parser.add_argument(
        "--allow-empty-evidence",
        action="store_true",
        help="Allow promotion without evidence_ref.",
    )
    parser.add_argument(
        "--allow-missing-raw",
        action="store_true",
        help="Allow missing RawAsset records.",
    )
    parser.add_argument(
        "--note",
        default="",
        help="Version note for pattern snapshot.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no DB writes.")
    args = parser.parse_args()

    result = await run_pattern_promotion(
        derive_from_evidence=args.derive_from_evidence,
        min_confidence=args.min_confidence,
        min_sources=args.min_sources,
        allow_empty_evidence=args.allow_empty_evidence,
        allow_missing_raw=args.allow_missing_raw,
        note=args.note,
        dry_run=args.dry_run,
    )

    print("Promotion summary:", result.get("stats"))
    if result.get("derived_candidates"):
        print(f"Derived candidates created: {result['derived_candidates']}")
    if result.get("pattern_version"):
        print(f"patternVersion bumped to {result['pattern_version']}")


if __name__ == "__main__":
    asyncio.run(main())
