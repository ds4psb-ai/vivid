#!/usr/bin/env python3
"""Backfill standardized agent artifacts from legacy tool payloads."""
from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List

from sqlalchemy import select

from app.agents.artifact_backfill import derive_artifacts_from_tool_payload
from app.database import AsyncSessionLocal, init_db
from app.models import AgentArtifact


def _fingerprint(payload: Dict) -> str:
    try:
        return json.dumps(payload, sort_keys=True, default=str)
    except TypeError:
        return str(payload)


def _parse_datetime(value: str) -> datetime:
    trimmed = value.strip()
    if trimmed.endswith("Z"):
        trimmed = trimmed.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(trimmed)
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


async def backfill(
    session_id: str | None,
    commit: bool,
    limit: int | None,
    since: str | None,
    until: str | None,
    artifact_types: List[str],
) -> None:
    await init_db(drop_all=False)
    async with AsyncSessionLocal() as db:
        query = select(AgentArtifact).order_by(AgentArtifact.created_at.asc())
        if session_id:
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError as exc:
                raise SystemExit(f"Invalid session id: {session_id}") from exc
            query = query.where(AgentArtifact.session_id == session_uuid)
        if since:
            query = query.where(AgentArtifact.created_at >= _parse_datetime(since))
        if until:
            query = query.where(AgentArtifact.created_at <= _parse_datetime(until))
        if artifact_types:
            query = query.where(AgentArtifact.artifact_type.in_(artifact_types))
        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        artifacts = result.scalars().all()
        sessions: Dict[str, List[AgentArtifact]] = defaultdict(list)
        for artifact in artifacts:
            sessions[str(artifact.session_id)].append(artifact)

        total_new = 0
        total_sessions = len(sessions)
        for session_key, session_artifacts in sessions.items():
            existing_payloads = set()
            for artifact in session_artifacts:
                if isinstance(artifact.payload, dict):
                    existing_payloads.add(_fingerprint(artifact.payload))

            new_rows: List[AgentArtifact] = []
            for artifact in session_artifacts:
                if not isinstance(artifact.payload, dict):
                    continue
                if "artifact_type" in artifact.payload:
                    continue
                derived_payloads = derive_artifacts_from_tool_payload(
                    artifact.artifact_type,
                    artifact.payload,
                )
                for payload in derived_payloads:
                    fingerprint = _fingerprint(payload)
                    if fingerprint in existing_payloads:
                        continue
                    existing_payloads.add(fingerprint)
                    new_rows.append(
                        AgentArtifact(
                            session_id=artifact.session_id,
                            artifact_type=payload.get("artifact_type", "artifact"),
                            payload=payload,
                            version=1,
                        )
                    )

            if new_rows:
                total_new += len(new_rows)
                if commit:
                    db.add_all(new_rows)
                else:
                    print(f"[dry-run] {session_key}: +{len(new_rows)} artifacts")

        if commit and total_new:
            await db.commit()

        print(
            f"Backfill complete. sessions={total_sessions}, new_artifacts={total_new}, commit={commit}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill agent artifacts from tool payloads")
    parser.add_argument("--session-id", default=None, help="Target a specific session id")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of artifacts scanned")
    parser.add_argument("--commit", action="store_true", help="Persist changes to the database")
    parser.add_argument("--since", default=None, help="Filter by created_at >= (ISO timestamp)")
    parser.add_argument("--until", default=None, help="Filter by created_at <= (ISO timestamp)")
    parser.add_argument(
        "--artifact-type",
        action="append",
        default=[],
        help="Filter by artifact_type (repeatable)",
    )
    args = parser.parse_args()
    asyncio.run(
        backfill(
            args.session_id,
            args.commit,
            args.limit,
            args.since,
            args.until,
            args.artifact_type,
        )
    )


if __name__ == "__main__":
    main()
