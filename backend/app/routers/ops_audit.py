"""Ops audit log router."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models import OpsActionLog


router = APIRouter(prefix="/ops", tags=["ops"])


class OpsActionLogResponse(BaseModel):
    id: str
    action_type: str
    status: str
    note: Optional[str] = None
    payload: dict
    stats: dict
    duration_ms: Optional[int] = None
    actor_id: Optional[str] = None
    created_at: str


@router.get("/audit", response_model=list[OpsActionLogResponse])
async def list_ops_audit_logs(
    action_type: Optional[str] = Query(default=None),
    actor_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin_user: dict = Depends(require_admin),
):
    """List ops action logs (admin only)."""
    query = select(OpsActionLog)

    if action_type:
        query = query.where(OpsActionLog.action_type == action_type)
    if actor_id:
        query = query.where(OpsActionLog.actor_id == actor_id)
    if status:
        query = query.where(OpsActionLog.status == status)

    result = await db.execute(
        query.order_by(OpsActionLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()

    return [
        OpsActionLogResponse(
            id=str(log.id),
            action_type=log.action_type,
            status=log.status,
            note=log.note,
            payload=log.payload or {},
            stats=log.stats or {},
            duration_ms=log.duration_ms,
            actor_id=log.actor_id,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]
