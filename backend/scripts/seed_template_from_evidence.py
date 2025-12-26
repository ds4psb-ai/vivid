"""Seed a template graph from EvidenceRecord entries."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal
from app.template_seeding import seed_template_from_evidence


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed a template from evidence records.")
    parser.add_argument("--notebook-id", required=True, help="Notebook id to source evidence")
    parser.add_argument("--slug", required=True, help="Template slug")
    parser.add_argument("--title", required=True, help="Template title")
    parser.add_argument("--description", default="Seeded template", help="Template description")
    parser.add_argument("--capsule-key", required=True, help="Capsule key")
    parser.add_argument("--capsule-version", required=True, help="Capsule version")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--public", action="store_true", help="Make template public")
    return parser.parse_args()


async def _run() -> None:
    args = _parse_args()
    tags: List[str] = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    async with AsyncSessionLocal() as session:
        await seed_template_from_evidence(
            session,
            slug=args.slug,
            title=args.title,
            description=args.description,
            capsule_key=args.capsule_key,
            capsule_version=args.capsule_version,
            notebook_id=args.notebook_id,
            tags=tags if tags else None,
            is_public=args.public,
        )


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
