#!/usr/bin/env python3
"""
Generate App/Dimension color tokens from AppRegistry YAML.

Usage:
  python scripts/generate_app_colors.py \
    --input config/apps/content/dimensions \
    --output tokens/app_colors.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import yaml


def stable_hue(seed: str) -> int:
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
    value = int(digest[:8], 16)
    return value % 360


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalize_app_id(name: str) -> str:
    return name.strip().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate app color tokens from YAML")
    parser.add_argument("--input", required=True, help="Directory with app YAML files")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    input_dir = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    colors: Dict[str, Any] = {}
    for yaml_path in sorted(input_dir.glob("*.yaml")):
        data = load_yaml(yaml_path)
        name = data.get("metadata", {}).get("name")
        if not name:
            continue
        app_id = normalize_app_id(name)
        hue = stable_hue(app_id)
        colors[app_id] = {
            "hue": hue,
            "chroma": 0.18,
            "L": {"light": 0.52, "dark": 0.64},
            "source": str(yaml_path.relative_to(input_dir.parent.parent.parent)),
        }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "config/apps/content/dimensions/*.yaml",
        "strategy": "stable-hash-hue + fixed chroma/lightness",
        "app_colors": colors,
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
