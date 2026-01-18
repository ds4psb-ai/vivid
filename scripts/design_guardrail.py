#!/usr/bin/env python3
"""
Design Guardrail Scanner
- Detects hardcoded color literals in frontend source.
- Compares against a baseline snapshot to prevent regressions.

Usage:
  python scripts/design_guardrail.py --root frontend/src --baseline docs/design/
  python scripts/design_guardrail.py --root frontend/src --baseline docs/design/ --update-baseline
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Dict, Any

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}")
RGB_RE = re.compile(r"rgba?\([^\)]*\)")
HSL_RE = re.compile(r"hsla?\([^\)]*\)")
OK_RE = re.compile(r"oklch\([^\)]*\)|oklab\([^\)]*\)")

DEFAULT_EXTS = {".ts", ".tsx", ".css", ".scss"}
EXCLUDE_DIRS = {"node_modules", ".next", ".git", "dist", "build"}


@dataclass(frozen=True)
class Match:
    path: str
    line: int
    literal: str
    kind: str


def iter_files(root: Path, exts: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_dir():
            if path.name in EXCLUDE_DIRS:
                # skip directory subtree
                continue
        if path.is_file() and path.suffix in exts:
            # skip excluded dirs in path parts
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            yield path


def scan_file(path: Path, root: Path) -> List[Match]:
    matches: List[Match] = []
    rel = str(path.relative_to(root))
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
    for idx, line in enumerate(text.splitlines(), start=1):
        for regex, kind in (
            (HEX_RE, "hex"),
            (RGB_RE, "rgb"),
            (HSL_RE, "hsl"),
            (OK_RE, "ok"),
        ):
            for m in regex.finditer(line):
                matches.append(Match(path=rel, line=idx, literal=m.group(0), kind=kind))
    return matches


def scan_root(root: Path) -> List[Match]:
    results: List[Match] = []
    for path in iter_files(root, DEFAULT_EXTS):
        results.extend(scan_file(path, root))
    return results


def serialize(matches: List[Match]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for m in matches:
        counts[m.kind] = counts.get(m.kind, 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "matches": [
            {"path": m.path, "line": m.line, "literal": m.literal, "kind": m.kind}
            for m in matches
        ],
    }


def load_baseline(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(match: Dict[str, Any]) -> str:
    return f"{match['path']}:{match['line']}:{match['kind']}:{match['literal']}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Design guardrail scanner")
    parser.add_argument("--root", required=True, help="Root directory to scan (e.g. frontend/src)")
    parser.add_argument("--baseline", required=True, help="Baseline directory (e.g. docs/design)")
    parser.add_argument("--update-baseline", action="store_true", help="Overwrite baseline snapshot")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    baseline_dir = Path(args.baseline).resolve()
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = baseline_dir / "design_guardrail_baseline.json"

    matches = scan_root(root)
    snapshot = serialize(matches)

    if args.update_baseline or not baseline_path.exists():
        baseline_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Baseline written: {baseline_path}")
        return 0

    baseline = load_baseline(baseline_path) or {"matches": []}
    baseline_fps = {fingerprint(m) for m in baseline.get("matches", [])}
    current_fps = {fingerprint(m) for m in snapshot.get("matches", [])}

    new_entries = sorted(current_fps - baseline_fps)
    if new_entries:
        print("FAILED: New hardcoded color literals detected")
        for entry in new_entries[:50]:
            print("  +", entry)
        print(f"Total new entries: {len(new_entries)}")
        print("Run with --update-baseline only if intentional.")
        return 1

    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
