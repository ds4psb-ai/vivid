"""Demo runner for promoting mock Sheets data into DB SoR."""
from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
import tempfile
from typing import Dict

from sqlalchemy import text
import sys


def _ensure_env_from_mock(mock_dir: Path) -> Path:
    os.environ.setdefault("SHEETS_MODE", "csv")
    os.environ.setdefault("VIVID_NOTEBOOK_LIBRARY_CSV_URL", str(mock_dir / "notebook_library.csv"))
    os.environ.setdefault("VIVID_RAW_ASSETS_CSV_URL", str(mock_dir / "raw_assets.csv"))
    os.environ.setdefault("VIVID_VIDEO_STRUCTURED_CSV_URL", str(mock_dir / "video_structured.csv"))
    os.environ.setdefault("VIVID_DERIVED_INSIGHTS_CSV_URL", str(mock_dir / "derived_insights.csv"))
    os.environ.setdefault("VIVID_PATTERN_CANDIDATES_CSV_URL", str(mock_dir / "pattern_candidates.csv"))
    os.environ.setdefault("VIVID_PATTERN_TRACE_CSV_URL", str(mock_dir / "pattern_trace.csv"))
    quarantine_path = Path(tempfile.gettempdir()) / "vivid_quarantine.csv"
    os.environ.setdefault("VIVID_QUARANTINE_CSV_PATH", str(quarantine_path))
    return quarantine_path


async def _count_table(table: str, session) -> int:
    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
    return int(result.scalar() or 0)


async def _snapshot_counts(session) -> Dict[str, int]:
    tables = [
        "notebook_library",
        "raw_assets",
        "video_segments",
        "evidence_records",
        "pattern_candidates",
        "patterns",
        "pattern_trace",
    ]
    counts: Dict[str, int] = {}
    for table in tables:
        counts[table] = await _count_table(table, session)
    return counts


def _count_quarantine_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    return max(len(lines) - 1, 0)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Promote mock Sheets data into DB SoR.")
    parser.add_argument(
        "--mock-dir",
        default=str(Path(__file__).resolve().parents[1] / "mock_sheets"),
        help="Path to mock_sheets directory",
    )
    parser.add_argument(
        "--drop-all",
        action="store_true",
        help="Drop and recreate tables before promotion (dev only).",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    sys.path.append(str(root))
    mock_dir = Path(args.mock_dir).expanduser()
    quarantine_path = _ensure_env_from_mock(mock_dir)
    if quarantine_path.exists():
        quarantine_path.unlink()

    from app.database import init_db, AsyncSessionLocal
    import importlib
    promote_from_sheets = importlib.import_module("scripts.promote_from_sheets")

    await init_db(drop_all=args.drop_all)
    async with AsyncSessionLocal() as session:
        before = await _snapshot_counts(session)
        await promote_from_sheets.main()
        after = await _snapshot_counts(session)

    print("Promotion demo summary:")
    for table in sorted(after.keys()):
        delta = after[table] - before.get(table, 0)
        print(f"- {table}: {after[table]} (delta +{delta})")
    print(f"- quarantine_rows: {_count_quarantine_rows(quarantine_path)}")


if __name__ == "__main__":
    asyncio.run(main())
