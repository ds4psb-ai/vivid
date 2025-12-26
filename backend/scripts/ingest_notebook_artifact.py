import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import Claim, ClaimEvidenceMap, EvidenceRef, TraceRecord


def _load_payload(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("Input JSON must be an object or list.")


def _require_str(row: Dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def _optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ValueError("time_start_ms/time_end_ms must be integer-like")


def _normalize_evidence_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("evidence_refs must be an array of objects")
        cleaned.append(
            {
                "evidence_id": _require_str(row, "evidence_id"),
                "kind": _require_str(row, "kind"),
                "source_id": _require_str(row, "source_id"),
                "segment_id": row.get("segment_id"),
                "shot_id": row.get("shot_id"),
                "time_start_ms": _optional_int(row.get("time_start_ms")),
                "time_end_ms": _optional_int(row.get("time_end_ms")),
                "source_hash": row.get("source_hash"),
                "tags": row.get("tags") or [],
                "notes": row.get("notes"),
            }
        )
    return cleaned


def _normalize_claim_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("claims must be an array of objects")
        claim_id = _require_str(row, "claim_id")
        claim_type = _require_str(row, "claim_type")
        statement = _require_str(row, "statement")
        evidence_refs = row.get("evidence_refs") or []
        if not isinstance(evidence_refs, list) or len(evidence_refs) < 2:
            raise ValueError("claims.evidence_refs must include at least 2 items")
        cleaned.append(
            {
                "claim_id": claim_id,
                "claim_type": claim_type,
                "statement": statement,
                "cluster_id": row.get("cluster_id"),
                "temporal_phase": row.get("temporal_phase"),
                "evidence_refs": evidence_refs,
                "weight": row.get("weight"),
            }
        )
    return cleaned


def _normalize_trace(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    if not isinstance(row, dict):
        raise ValueError("trace must be an object")
    return {
        "trace_id": _require_str(row, "trace_id"),
        "bundle_hash": _require_str(row, "bundle_hash"),
        "model_version": _require_str(row, "model_version"),
        "prompt_version": _require_str(row, "prompt_version"),
        "eval_scores": row.get("eval_scores") or {},
        "token_usage": row.get("token_usage") or {},
        "latency_ms": row.get("latency_ms"),
        "cost_usd_est": row.get("cost_usd_est"),
    }


async def _upsert_records(
    artifacts: List[Dict[str, Any]],
    *,
    dry_run: bool,
) -> int:
    created = 0
    async with AsyncSessionLocal() as session:
        for artifact in artifacts:
            evidence_rows = _normalize_evidence_rows(artifact.get("evidence_refs") or [])
            claim_rows = _normalize_claim_rows(artifact.get("claims") or [])
            trace_row = _normalize_trace(artifact.get("trace"))

            evidence_lookup: Dict[str, EvidenceRef] = {}
            for row in evidence_rows:
                result = await session.execute(
                    select(EvidenceRef).where(EvidenceRef.evidence_id == row["evidence_id"])
                )
                record = result.scalars().first()
                if not record:
                    record = EvidenceRef(
                        evidence_id=row["evidence_id"],
                        kind=row["kind"],
                        source_id=row["source_id"],
                    )
                    session.add(record)
                    created += 1
                record.kind = row["kind"]
                record.source_id = row["source_id"]
                record.segment_id = row.get("segment_id")
                record.shot_id = row.get("shot_id")
                record.time_start_ms = row.get("time_start_ms")
                record.time_end_ms = row.get("time_end_ms")
                record.source_hash = row.get("source_hash")
                record.tags = row.get("tags") or []
                record.notes = row.get("notes")
                evidence_lookup[row["evidence_id"]] = record

            for row in claim_rows:
                result = await session.execute(
                    select(Claim).where(Claim.claim_id == row["claim_id"])
                )
                claim = result.scalars().first()
                if not claim:
                    claim = Claim(
                        claim_id=row["claim_id"],
                        claim_type=row["claim_type"],
                        statement=row["statement"],
                    )
                    session.add(claim)
                    created += 1
                claim.claim_type = row["claim_type"]
                claim.statement = row["statement"]
                claim.cluster_id = row.get("cluster_id")
                claim.temporal_phase = row.get("temporal_phase")

                for evidence_id in row["evidence_refs"]:
                    if evidence_id not in evidence_lookup:
                        raise ValueError(f"Missing evidence_ref: {evidence_id}")
                    evidence = evidence_lookup[evidence_id]
                    result = await session.execute(
                        select(ClaimEvidenceMap).where(
                            ClaimEvidenceMap.claim_id == claim.id,
                            ClaimEvidenceMap.evidence_id == evidence.id,
                        )
                    )
                    mapping = result.scalars().first()
                    if not mapping:
                        mapping = ClaimEvidenceMap(
                            claim_id=claim.id,
                            evidence_id=evidence.id,
                        )
                        session.add(mapping)
                        created += 1
                    mapping.weight = row.get("weight")

            if trace_row:
                result = await session.execute(
                    select(TraceRecord).where(TraceRecord.trace_id == trace_row["trace_id"])
                )
                trace = result.scalars().first()
                if not trace:
                    trace = TraceRecord(
                        trace_id=trace_row["trace_id"],
                        bundle_hash=trace_row["bundle_hash"],
                        model_version=trace_row["model_version"],
                        prompt_version=trace_row["prompt_version"],
                    )
                    session.add(trace)
                    created += 1
                trace.bundle_hash = trace_row["bundle_hash"]
                trace.model_version = trace_row["model_version"]
                trace.prompt_version = trace_row["prompt_version"]
                trace.eval_scores = trace_row["eval_scores"] or {}
                trace.token_usage = trace_row["token_usage"] or {}
                trace.latency_ms = trace_row.get("latency_ms")
                trace.cost_usd_est = trace_row.get("cost_usd_est")

        if dry_run:
            await session.rollback()
        else:
            await session.commit()
    return created


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Ingest NotebookLM artifact JSON.")
    parser.add_argument("--input", required=True, help="Path to artifact JSON file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = _load_payload(Path(args.input))
    artifacts = _extract_rows(payload)

    await init_db()
    created = await _upsert_records(artifacts, dry_run=args.dry_run)
    print(f"ingest_notebook_artifact: upserted {created} records")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
