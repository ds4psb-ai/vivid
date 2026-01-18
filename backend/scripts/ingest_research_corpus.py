#!/usr/bin/env python3
"""Ingest Tavily research corpus JSON into Qdrant RAG collections.

Usage:
    # Ingest a single research output
    python scripts/ingest_research_corpus.py \
        --input data/source_packs/research/research_*.json \
        --dimension 4D \
        --dataset-id film_analysis \
        --app-key teaching.reference.analyze

    # Ingest a directory of research outputs with quality gating
    python scripts/ingest_research_corpus.py \
        --input data/source_packs/research/ \
        --min-score 0.55 \
        --min-quality standard \
        --allow-license permissive,unknown
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Add backend to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.rag.tier1_dimension_rag import DIMENSION_COLLECTIONS, get_dimension_rag


QUALITY_RANK = {"low": 0, "standard": 1, "high": 2}
DEFAULT_ALLOWED_LICENSES = {"permissive", "unknown"}


def _expand_inputs(raw_inputs: List[str]) -> List[Path]:
    paths: List[Path] = []
    for raw in raw_inputs:
        candidate = Path(raw)
        if candidate.is_dir():
            paths.extend(sorted(candidate.glob("*.json")))
        elif candidate.is_file():
            paths.append(candidate)
        else:
            raise SystemExit(f"Input not found: {candidate}")
    if not paths:
        raise SystemExit("No JSON inputs found.")
    return paths


def _load_payload(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("documents", "docs", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return [payload]
    raise ValueError("Input JSON must be a list or object.")


def _compute_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _resolve_dimension(row: Dict[str, Any], override: Optional[str]) -> Optional[str]:
    if override:
        return override.upper()
    dim = row.get("dimension") or row.get("dim")
    return dim.upper() if isinstance(dim, str) else None


def _quality_rank(value: Optional[str]) -> int:
    if not value:
        return -1
    return QUALITY_RANK.get(value.lower(), -1)


def _passes_gate(
    row: Dict[str, Any],
    *,
    min_score: float,
    min_quality: str,
    allowed_licenses: set[str],
    min_content_len: int,
) -> Tuple[bool, str]:
    content = (row.get("content") or "").strip()
    if len(content) < min_content_len:
        return False, "content_length"

    score = float(row.get("relevance_score") or 0)
    if score < min_score:
        return False, "relevance_score"

    license_status = (row.get("license_status") or "unknown").lower()
    if license_status not in allowed_licenses:
        return False, "license_status"

    if _quality_rank(row.get("quality_tier")) < _quality_rank(min_quality):
        return False, "quality_tier"

    return True, "ok"


def _build_metadata(
    row: Dict[str, Any],
    *,
    dataset_id: Optional[str],
    app_key: Optional[str],
    dimension: str,
    content_hash: str,
) -> Dict[str, Any]:
    metadata = {
        "source": row.get("source", "tavily_research"),
        "url": row.get("url"),
        "domain": row.get("source_domain"),
        "query": row.get("query"),
        "quality_tier": row.get("quality_tier"),
        "license_status": row.get("license_status"),
        "relevance_score": row.get("relevance_score"),
        "fetched_at": row.get("fetched_at"),
        "dimension": dimension,
        "content_hash": content_hash,
    }
    if row.get("auteur_key"):
        metadata["auteur_key"] = row.get("auteur_key")
    if row.get("tags"):
        metadata["tags"] = row.get("tags")
    if app_key or row.get("app_key"):
        metadata["app_key"] = app_key or row.get("app_key")
    if dataset_id or row.get("dataset_id"):
        metadata["dataset_id"] = dataset_id or row.get("dataset_id")
    return metadata


def _normalize_doc_id(row: Dict[str, Any], content_hash: str) -> str:
    return (
        row.get("id")
        or row.get("doc_id")
        or row.get("document_id")
        or f"research_{content_hash}"
    )


def ingest_documents(
    rows: Iterable[Dict[str, Any]],
    *,
    dimension_override: Optional[str],
    dataset_id: Optional[str],
    app_key: Optional[str],
    min_score: float,
    min_quality: str,
    allowed_licenses: set[str],
    min_content_len: int,
    dry_run: bool,
) -> Dict[str, Any]:
    stats = {
        "loaded": 0,
        "eligible": 0,
        "indexed": 0,
        "skipped": {
            "content_length": 0,
            "relevance_score": 0,
            "license_status": 0,
            "quality_tier": 0,
            "invalid_dimension": 0,
        },
    }

    seen_hashes: set[str] = set()
    rag_cache: Dict[str, Any] = {}

    for row in rows:
        stats["loaded"] += 1
        if not isinstance(row, dict):
            stats["skipped"]["content_length"] += 1
            continue

        dimension = _resolve_dimension(row, dimension_override)
        if not dimension or dimension not in DIMENSION_COLLECTIONS:
            stats["skipped"]["invalid_dimension"] += 1
            continue

        content = (row.get("content") or "").strip()
        if not content:
            stats["skipped"]["content_length"] += 1
            continue

        content_hash = row.get("content_hash") or _compute_hash(content)
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)

        ok, reason = _passes_gate(
            row,
            min_score=min_score,
            min_quality=min_quality,
            allowed_licenses=allowed_licenses,
            min_content_len=min_content_len,
        )
        if not ok:
            stats["skipped"][reason] += 1
            continue

        stats["eligible"] += 1
        if dry_run:
            continue

        rag = rag_cache.get(dimension)
        if rag is None:
            rag = get_dimension_rag(dimension)
            if rag.client is None:
                stats["skipped"]["invalid_dimension"] += 1
                continue
            rag.ensure_collection()
            rag_cache[dimension] = rag

        doc_id = _normalize_doc_id(row, content_hash)
        title = (row.get("title") or "").strip()
        content_payload = f"{title}\n\n{content}" if title else content
        metadata = _build_metadata(
            row,
            dataset_id=dataset_id,
            app_key=app_key,
            dimension=dimension,
            content_hash=content_hash,
        )

        if rag.index_document(doc_id, content_payload, metadata=metadata):
            stats["indexed"] += 1

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest research corpus into RAG.")
    parser.add_argument("--input", nargs="+", required=True, help="Input JSON file(s) or dir.")
    parser.add_argument("--dimension", help="Override dimension for all docs (e.g., 4D).")
    parser.add_argument("--dataset-id", help="dataset_id metadata (optional).")
    parser.add_argument("--app-key", help="app_key metadata (optional).")
    parser.add_argument("--min-score", type=float, default=0.55, help="Minimum relevance score.")
    parser.add_argument(
        "--min-quality",
        default="standard",
        choices=["low", "standard", "high"],
        help="Minimum quality tier.",
    )
    parser.add_argument(
        "--allow-license",
        default="permissive,unknown",
        help="Comma-separated allowed license statuses.",
    )
    parser.add_argument("--min-content-len", type=int, default=200, help="Minimum content length.")
    parser.add_argument("--dry-run", action="store_true", help="Validate only; no indexing.")
    args = parser.parse_args()

    allowed_licenses = {item.strip().lower() for item in args.allow_license.split(",") if item.strip()}
    if not allowed_licenses:
        allowed_licenses = DEFAULT_ALLOWED_LICENSES

    rows: List[Dict[str, Any]] = []
    for path in _expand_inputs(args.input):
        payload = _load_payload(path)
        rows.extend(_extract_rows(payload))

    stats = ingest_documents(
        rows,
        dimension_override=args.dimension,
        dataset_id=args.dataset_id,
        app_key=args.app_key,
        min_score=args.min_score,
        min_quality=args.min_quality,
        allowed_licenses=allowed_licenses,
        min_content_len=args.min_content_len,
        dry_run=args.dry_run,
    )

    mode = "DRY RUN" if args.dry_run else "INDEX"
    print(f"[{mode}] Loaded: {stats['loaded']} | Eligible: {stats['eligible']} | Indexed: {stats['indexed']}")
    print(f"Skipped: {stats['skipped']}")


if __name__ == "__main__":
    main()
