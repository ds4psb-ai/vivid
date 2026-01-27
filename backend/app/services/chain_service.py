"""Chain Session Service - Business logic for chain persistence.

Provides:
- CRUD operations for chain sessions
- Optimistic locking for concurrent updates
- Previous run lookup for dimension data
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChainSession, CapsuleRun
from app.schemas.chain import (
    ChainDataOutput,
    ChainSessionCreate,
    ChainSessionUpdate,
    ChainSessionResponse,
    ChainSessionListItem,
    PreviousRunResponse,
)

logger = logging.getLogger(__name__)


async def create_chain_session(
    db: AsyncSession,
    user_id: str,
    data: ChainSessionCreate,
) -> ChainSession:
    """Create a new chain session.

    Args:
        db: Database session
        user_id: Owner user ID
        data: Creation request data

    Returns:
        Created ChainSession model
    """
    session = ChainSession(
        user_id=user_id,
        mega_app=data.mega_app,
        title=data.title,
        ip_slug=data.ip_slug,
        chain_data={},
        accumulated_evidence_refs=[],
        navigation_history=[],
        version=1,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"[ChainService] Created session {session.id} for user {user_id}")
    return session


async def get_chain_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: str,
) -> Optional[ChainSession]:
    """Get a chain session by ID, verifying ownership.

    Args:
        db: Database session
        session_id: Session UUID
        user_id: Owner user ID (for BOLA prevention)

    Returns:
        ChainSession if found and owned by user, None otherwise
    """
    stmt = select(ChainSession).where(
        ChainSession.id == session_id,
        ChainSession.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_chain_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    update_data: ChainSessionUpdate,
    user_id: str,
) -> ChainSession:
    """Update a chain session with optimistic locking.

    Uses version field to prevent race conditions:
    - Client sends their current version
    - Server compares with DB version
    - If mismatch, returns 409 Conflict

    Args:
        db: Database session
        session_id: Session UUID
        update_data: Update request with version
        user_id: Owner user ID

    Returns:
        Updated ChainSession

    Raises:
        HTTPException 404: Session not found
        HTTPException 409: Version conflict
    """
    # Build update values dict
    update_values: dict = {
        "updated_at": datetime.utcnow(),
        "version": ChainSession.version + 1,
    }

    # Add optional fields if provided
    if update_data.chain_data is not None:
        # Convert Pydantic models to dicts for JSONB storage
        update_values["chain_data"] = {
            key: val.model_dump(mode="json") if hasattr(val, "model_dump") else val
            for key, val in update_data.chain_data.items()
        }

    if update_data.accumulated_evidence_refs is not None:
        update_values["accumulated_evidence_refs"] = update_data.accumulated_evidence_refs

    if update_data.current_dimension is not None:
        update_values["current_dimension"] = update_data.current_dimension

    if update_data.navigation_history is not None:
        update_values["navigation_history"] = update_data.navigation_history

    if update_data.title is not None:
        update_values["title"] = update_data.title

    # Execute optimistic lock update
    stmt = (
        update(ChainSession)
        .where(
            ChainSession.id == session_id,
            ChainSession.user_id == user_id,
            ChainSession.version == update_data.version,  # Optimistic lock check
        )
        .values(**update_values)
        .returning(ChainSession)
    )

    result = await db.execute(stmt)
    updated = result.scalar_one_or_none()

    if not updated:
        # Determine if it's a version conflict or not found
        existing = await db.get(ChainSession, session_id)

        if existing is None:
            raise HTTPException(status_code=404, detail="Chain session not found")

        if existing.user_id != user_id:
            # BOLA prevention - don't reveal session exists
            raise HTTPException(status_code=404, detail="Chain session not found")

        # Version conflict
        logger.warning(
            f"[ChainService] Version conflict for session {session_id}: "
            f"server={existing.version}, client={update_data.version}"
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "VERSION_CONFLICT",
                "server_version": existing.version,
                "your_version": update_data.version,
                "message": "Session was modified by another client. Please refresh and retry.",
            },
        )

    await db.commit()
    await db.refresh(updated)

    logger.info(f"[ChainService] Updated session {session_id} to version {updated.version}")
    return updated


async def list_user_sessions(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> list[ChainSessionListItem]:
    """List chain sessions for a user, ordered by most recent.

    Args:
        db: Database session
        user_id: Owner user ID
        limit: Max results (default 20)
        offset: Pagination offset

    Returns:
        List of abbreviated session items
    """
    stmt = (
        select(ChainSession)
        .where(ChainSession.user_id == user_id)
        .order_by(ChainSession.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    return [
        ChainSessionListItem(
            id=s.id,
            title=s.title,
            mega_app=s.mega_app,
            ip_slug=s.ip_slug,
            version=s.version,
            current_dimension=s.current_dimension,
            dimension_count=len(s.chain_data) if s.chain_data else 0,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


async def delete_chain_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: str,
) -> bool:
    """Delete a chain session.

    Args:
        db: Database session
        session_id: Session UUID
        user_id: Owner user ID

    Returns:
        True if deleted, False if not found
    """
    session = await get_chain_session(db, session_id, user_id)
    if not session:
        return False

    await db.delete(session)
    await db.commit()

    logger.info(f"[ChainService] Deleted session {session_id}")
    return True


async def get_previous_run_for_dimension(
    db: AsyncSession,
    user_id: str,
    dimension_key: str,
) -> PreviousRunResponse:
    """Get the most recent capsule run output for a dimension.

    Looks up the most recent successful CapsuleRun for the given
    dimension and user, returning its output data.

    Args:
        db: Database session
        user_id: Owner user ID
        dimension_key: Dimension route key (e.g., 'reference-decoder')

    Returns:
        PreviousRunResponse with run data if found
    """
    # Map dimension keys to capsule keys
    dimension_to_capsule = {
        "reference-decoder": "reference_decoder",
        "story-architect": "story_architect",
        "aesthetic-director": "aesthetic_director",
        "storyboard-sketch": "storyboard_sketch",
        "sound-crafter": "sound_crafter",
        "prompt-alchemy": "prompt_alchemy",
        "visual-realizer": "visual_realizer",
        "video-maker": "video_maker",
        "quality-director": "quality_director",
        "abyss-mirror": "abyss_mirror",
    }

    capsule_key = dimension_to_capsule.get(dimension_key)
    if not capsule_key:
        # Unknown dimension - return empty
        return PreviousRunResponse(
            dimension_key=dimension_key,
            found=False,
        )

    # Find most recent successful run
    stmt = (
        select(CapsuleRun)
        .where(
            CapsuleRun.user_id == user_id,
            CapsuleRun.capsule_key == capsule_key,
            CapsuleRun.status == "success",
        )
        .order_by(CapsuleRun.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()

    if not run:
        return PreviousRunResponse(
            dimension_key=dimension_key,
            found=False,
        )

    # Extract output from summary
    output = run.summary.get("output", {}) if run.summary else {}

    return PreviousRunResponse(
        run_id=run.id,
        dimension_key=dimension_key,
        output=output,
        evidence_refs=run.evidence_refs or [],
        created_at=run.created_at,
        found=True,
    )


def model_to_response(session: ChainSession) -> ChainSessionResponse:
    """Convert ChainSession model to response schema.

    Args:
        session: ChainSession model

    Returns:
        ChainSessionResponse schema
    """
    # Convert raw chain_data dicts to ChainDataOutput objects
    chain_data_typed: dict[str, ChainDataOutput] = {}
    if session.chain_data:
        for key, value in session.chain_data.items():
            if isinstance(value, dict):
                chain_data_typed[key] = ChainDataOutput(**value)

    return ChainSessionResponse(
        id=session.id,
        user_id=session.user_id,
        chain_data=chain_data_typed,
        accumulated_evidence_refs=session.accumulated_evidence_refs or [],
        current_dimension=session.current_dimension,
        navigation_history=session.navigation_history or [],
        mega_app=session.mega_app,
        title=session.title,
        ip_slug=session.ip_slug,
        version=session.version,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
