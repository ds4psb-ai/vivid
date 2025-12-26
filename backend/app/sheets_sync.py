"""Run Sheets Bus -> DB SoR sync for ops automation."""
from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import Dict


def _load_promote_module():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "promote_from_sheets.py"
    spec = importlib.util.spec_from_file_location("promote_from_sheets", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load promote_from_sheets module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module


async def run_sheets_sync() -> Dict[str, int]:
    module = _load_promote_module()
    start = time.perf_counter()
    await module.main()
    duration_ms = int((time.perf_counter() - start) * 1000)
    return {"duration_ms": duration_ms}
