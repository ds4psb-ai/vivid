import argparse
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import init_db
from app.pattern_versioning import refresh_capsule_specs


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a new CapsuleSpec version with the latest patternVersion."
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
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Also update inactive capsule specs (default updates active only).",
    )
    args = parser.parse_args()

    await init_db()
    pattern_version = args.pattern_version.strip() if args.pattern_version else None
    pattern_version, updated = await refresh_capsule_specs(
        pattern_version,
        dry_run=args.dry_run,
        only_active=not args.include_inactive,
    )

    mode = "dry-run" if args.dry_run else "updated"
    print(f"{mode}: {updated} capsule specs -> patternVersion={pattern_version}")


if __name__ == "__main__":
    asyncio.run(main())
