import argparse
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import CapsuleSpec
from app.patterns import get_latest_pattern_version


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync CapsuleSpec patternVersion to the latest PatternVersion snapshot."
    )
    parser.add_argument(
        "--pattern-version",
        help="Override the target patternVersion (defaults to latest snapshot).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the number of capsules to update without writing.",
    )
    args = parser.parse_args()

    await init_db()
    async with AsyncSessionLocal() as session:
        if args.pattern_version:
            pattern_version = args.pattern_version.strip()
        else:
            pattern_version = await get_latest_pattern_version(session)

        result = await session.execute(select(CapsuleSpec))
        specs = result.scalars().all()
        updated = 0
        for spec in specs:
            payload = spec.spec or {}
            current = payload.get("patternVersion") or payload.get("pattern_version")
            if current == pattern_version:
                continue
            payload["patternVersion"] = pattern_version
            spec.spec = payload
            updated += 1

        if args.dry_run:
            await session.rollback()
        else:
            await session.commit()

    mode = "dry-run" if args.dry_run else "updated"
    print(f"{mode}: {updated} capsule specs -> patternVersion={pattern_version}")


if __name__ == "__main__":
    asyncio.run(main())
