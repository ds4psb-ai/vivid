"""Academy access request endpoints.

Allows logged-in users to request Academy access without
having to manually comment their email in KakaoTalk.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_authenticated_user
from app.models import AccessRequest

router = APIRouter()


class AccessRequestCreate(BaseModel):
    """Request body for creating access request."""
    name: Optional[str] = None  # Optional depositor name for matching


class AccessRequestResponse(BaseModel):
    """Response for access request status."""
    status: str
    email: str
    name: Optional[str] = None
    created_at: datetime
    message: str


@router.post("")
async def create_access_request(
    body: AccessRequestCreate,
    user: dict = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Create an Academy access request.
    
    Stores the user's email from their Google session for admin review.
    Prevents duplicate requests from the same user.
    """
    user_id = user.get("user_id")
    email = user.get("email", "")
    session_name = user.get("name", "")
    
    if not user_id or not email:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    # Check for existing request
    result = await db.execute(
        select(AccessRequest).where(AccessRequest.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Already requested - return current status
        return JSONResponse({
            "status": existing.status,
            "email": existing.email,
            "name": existing.name,
            "created_at": existing.created_at.isoformat(),
            "message": "이미 접근 요청이 있습니다." if existing.status == "pending" else "요청이 처리되었습니다.",
            "already_exists": True,
        })
    
    # Create new request
    access_request = AccessRequest(
        user_id=user_id,
        email=email.lower(),
        name=body.name or session_name,
        status="pending",
    )
    db.add(access_request)
    await db.commit()
    await db.refresh(access_request)
    
    return JSONResponse({
        "status": "pending",
        "email": access_request.email,
        "name": access_request.name,
        "created_at": access_request.created_at.isoformat(),
        "message": "접근 요청이 접수되었습니다. 확인 후 연락드리겠습니다.",
        "already_exists": False,
    }, status_code=201)


@router.get("/status")
async def get_access_request_status(
    user: dict = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Get current user's access request status."""
    user_id = user.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    result = await db.execute(
        select(AccessRequest).where(AccessRequest.user_id == user_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        return JSONResponse({
            "has_request": False,
            "status": None,
            "message": "접근 요청 내역이 없습니다.",
        })
    
    status_messages = {
        "pending": "접근 요청이 대기 중입니다.",
        "approved": "접근이 승인되었습니다.",
        "rejected": "접근 요청이 거절되었습니다.",
    }
    
    return JSONResponse({
        "has_request": True,
        "status": request.status,
        "email": request.email,
        "name": request.name,
        "created_at": request.created_at.isoformat(),
        "message": status_messages.get(request.status, "알 수 없는 상태"),
    })


# ============================================
# Admin Endpoints (Master Admin Only)
# ============================================

from app.config import settings


async def require_admin_user(
    user: dict = Depends(require_authenticated_user),
) -> dict:
    """Require master admin access."""
    email = user.get("email", "").lower()
    if email not in settings.MASTER_ADMIN_EMAIL_SET:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


class AdminAccessRequestItem(BaseModel):
    """Response item for admin list."""
    id: str
    user_id: str
    email: str
    name: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class AdminListResponse(BaseModel):
    """Response for admin list."""
    requests: list[AdminAccessRequestItem]
    total: int
    pending_count: int


class AdminActionRequest(BaseModel):
    """Request for approve/reject action."""
    notes: Optional[str] = None


@router.get("/admin/list")
async def admin_list_access_requests(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _admin: dict = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """List all access requests (admin only)."""
    from sqlalchemy import func
    
    # Build query
    query = select(AccessRequest).order_by(AccessRequest.created_at.desc())
    if status:
        query = query.where(AccessRequest.status == status)
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    # Get counts
    total_result = await db.execute(select(func.count(AccessRequest.id)))
    total = total_result.scalar() or 0
    
    pending_result = await db.execute(
        select(func.count(AccessRequest.id)).where(AccessRequest.status == "pending")
    )
    pending_count = pending_result.scalar() or 0
    
    return JSONResponse({
        "requests": [
            {
                "id": str(r.id),
                "user_id": r.user_id,
                "email": r.email,
                "name": r.name,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in requests
        ],
        "total": total,
        "pending_count": pending_count,
    })


@router.patch("/admin/{request_id}/approve")
async def admin_approve_request(
    request_id: str,
    body: AdminActionRequest = AdminActionRequest(),
    _admin: dict = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Approve an access request (admin only).

    Also auto-creates a CrebitApplication with status='paid' if not exists.
    """
    from uuid import UUID
    from datetime import datetime
    from app.models import CrebitApplication, UserAccount

    try:
        rid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID")

    result = await db.execute(
        select(AccessRequest).where(AccessRequest.id == rid)
    )
    request = result.scalar_one_or_none()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    request.status = "approved"
    if body.notes:
        request.admin_notes = body.notes

    # Auto-create CrebitApplication if not exists
    application_created = False
    existing_app = await db.execute(
        select(CrebitApplication)
        .where(CrebitApplication.owner_id == request.user_id)
        .where(CrebitApplication.status == "paid")
    )
    if not existing_app.scalar_one_or_none():
        new_app = CrebitApplication(
            name=request.name or request.email.split("@")[0],
            email=request.email,
            phone="",
            track="A",
            status="paid",
            owner_id=request.user_id,
            paid_at=datetime.utcnow(),
            cohort="1기",
            notes="AccessRequest 승인으로 자동 생성",
        )
        db.add(new_app)
        application_created = True

    await db.commit()

    return JSONResponse({
        "success": True,
        "message": f"Request for {request.email} approved",
        "application_created": application_created,
    })


@router.patch("/admin/{request_id}/reject")
async def admin_reject_request(
    request_id: str,
    body: AdminActionRequest = AdminActionRequest(),
    _admin: dict = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Reject an access request (admin only)."""
    from uuid import UUID

    try:
        rid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID")

    result = await db.execute(
        select(AccessRequest).where(AccessRequest.id == rid)
    )
    request = result.scalar_one_or_none()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    request.status = "rejected"
    if body.notes:
        request.admin_notes = body.notes
    await db.commit()

    return JSONResponse({
        "success": True,
        "message": f"Request for {request.email} rejected",
    })


@router.patch("/admin/{request_id}/revoke")
async def admin_revoke_request(
    request_id: str,
    body: AdminActionRequest = AdminActionRequest(),
    _admin: dict = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Revoke an approved access request (admin only).

    Reverts approved status to rejected and deactivates linked CrebitApplication.
    """
    from uuid import UUID
    from app.models import CrebitApplication

    try:
        rid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID")

    result = await db.execute(
        select(AccessRequest).where(AccessRequest.id == rid)
    )
    request = result.scalar_one_or_none()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status != "approved":
        raise HTTPException(status_code=400, detail="Only approved requests can be revoked")

    # Revoke access request
    request.status = "rejected"
    request.admin_notes = (body.notes or "") + " [승인 취소됨]"

    # Deactivate linked CrebitApplication
    application_deactivated = False
    app_result = await db.execute(
        select(CrebitApplication)
        .where(CrebitApplication.owner_id == request.user_id)
        .where(CrebitApplication.status == "paid")
    )
    application = app_result.scalar_one_or_none()

    if application:
        application.status = "cancelled"
        application.owner_id = None
        application.notes = (application.notes or "") + " [승인 취소로 비활성화됨]"
        application_deactivated = True

    await db.commit()

    return JSONResponse({
        "success": True,
        "message": f"Request for {request.email} revoked",
        "application_deactivated": application_deactivated,
    })
