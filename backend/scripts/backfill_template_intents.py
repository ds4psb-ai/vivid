import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models_singularity import BlackholeTemplate
from app.resolvers.integration import extract_intent_from_preset


def _normalize_preset(preset: Dict[str, Any]) -> Dict[str, Any]:
    """Remove legacy-only keys before intent backfill."""
    if "legacy_params" in preset:
        preset = dict(preset)
        preset.pop("legacy_params", None)
    return preset


async def _backfill(session: AsyncSessionLocal, execute: bool) -> Dict[str, int]:
    result = await session.execute(select(BlackholeTemplate))
    templates = result.scalars().all()
    stats = {
        "checked": 0,
        "already_new": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": 0,
    }

    for template in templates:
        stats["checked"] += 1
        input_preset = template.input_preset or {}
        if not isinstance(input_preset, dict) or not input_preset:
            stats["skipped"] += 1
            continue

        input_preset = _normalize_preset(input_preset)

        if "intent" in input_preset and "schema_version" in input_preset:
            stats["already_new"] += 1
            continue

        try:
            intent = extract_intent_from_preset(input_preset)
        except Exception:
            stats["errors"] += 1
            continue

        if not intent:
            stats["skipped"] += 1
            continue

        next_preset = {
            "intent": intent.model_dump(),
            "schema_version": "2.0",
        }

        if execute:
            template.input_preset = next_preset
        stats["migrated"] += 1

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill BlackholeTemplate.input_preset to intent-based schema.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply updates to the database (default: dry-run).",
    )
    args = parser.parse_args()

    await init_db()
    async with AsyncSessionLocal() as session:
        stats = await _backfill(session, args.execute)
        if args.execute:
            await session.commit()

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"[{mode}] Backfill template intents: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
