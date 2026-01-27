"""Chain Session API - Workflow chain data persistence.

Provides endpoints for:
- Chain session CRUD operations
- Optimistic locking for concurrent updates
- Previous run lookup for dimension data

All endpoints require authentication and enforce user ownership (BOLA prevention).
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_user_id
from app.schemas.chain import (
    ChainSessionCreate,
    ChainSessionUpdate,
    ChainSessionResponse,
    ChainSessionListItem,
    PreviousRunResponse,
)
from app.services import chain_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chain", tags=["chain"])


@router.post("/session", response_model=ChainSessionResponse, status_code=201)
async def create_session(
    data: ChainSessionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_user_id),
) -> ChainSessionResponse:
    """Create a new chain session.

    Creates an empty chain session that can be populated with dimension
    outputs as the user progresses through the workflow.

    Args:
        data: Session creation request
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Created session with version=1
    """
    session = await chain_service.create_chain_session(db, user_id, data)
    return chain_service.model_to_response(session)


@router.get("/session/{session_id}", response_model=ChainSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_user_id),
) -> ChainSessionResponse:
    """Get a chain session by ID.

    Args:
        session_id: Session UUID
        db: Database session
        user_id: Authenticated user ID (for ownership verification)

    Returns:
        Chain session data including version for optimistic locking

    Raises:
        404: Session not found or not owned by user
    """
    session = await chain_service.get_chain_session(db, session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chain session not found")
    return chain_service.model_to_response(session)


@router.put("/session/{session_id}", response_model=ChainSessionResponse)
async def update_session(
    session_id: uuid.UUID,
    data: ChainSessionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_user_id),
) -> ChainSessionResponse:
    """Update a chain session with optimistic locking.

    Requires the current version in the request body. If the server's
    version differs, returns 409 Conflict with both versions.

    Args:
        session_id: Session UUID
        data: Update request with version (required)
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Updated session with incremented version

    Raises:
        404: Session not found or not owned by user
        409: Version conflict - session was modified by another client
    """
    session = await chain_service.update_chain_session(db, session_id, data, user_id)
    return chain_service.model_to_response(session)


@router.delete("/session/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_user_id),
) -> None:
    """Delete a chain session.

    Args:
        session_id: Session UUID
        db: Database session
        user_id: Authenticated user ID

    Raises:
        404: Session not found or not owned by user
    """
    deleted = await chain_service.delete_chain_session(db, session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chain session not found")


@router.get("/user", response_model=list[ChainSessionListItem])
async def list_user_sessions(
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_user_id),
) -> list[ChainSessionListItem]:
    """List chain sessions for the current user.

    Returns sessions ordered by most recently updated, with abbreviated
    data suitable for list views.

    Args:
        limit: Max results (1-100, default 20)
        offset: Pagination offset
        db: Database session
        user_id: Authenticated user ID

    Returns:
        List of session summaries
    """
    return await chain_service.list_user_sessions(db, user_id, limit, offset)


@router.get("/{app}/previous-run", response_model=PreviousRunResponse)
async def get_previous_run(
    app: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_user_id),
) -> PreviousRunResponse:
    """Get the most recent successful run for a dimension.

    Looks up the most recent CapsuleRun for the given dimension and user,
    returning its output data for use in downstream dimensions.

    Args:
        app: Dimension route key (e.g., 'reference-decoder')
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Previous run output if found, empty response otherwise
    """
    return await chain_service.get_previous_run_for_dimension(db, user_id, app)
