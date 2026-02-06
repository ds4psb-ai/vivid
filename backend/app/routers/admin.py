"""
Admin Router

내부 직원용 앱 관리 API
- 앱 등록/배포
- 앱 목록/상세
- 상태 관리
- 미리보기
"""
from __future__ import annotations

import base64
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.auth import require_user_id, get_is_admin
from app.services.app_registry import (
    get_app_registry,
    AppRegistryService,
    AppStatus,
    AppManifest,
)
from app.utils.error_sanitize import safe_error_detail


router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================
# Request/Response Models
# ============================================

class DimensionThemeRequest(BaseModel):
    theme: str = "default"
    primaryColor: str = "#84cc16"
    accentColor: str = "#22c55e"
    borderStyle: str = "solid"


class CreditsRequest(BaseModel):
    perRun: int = 0
    perSave: int = 0
    perMinute: int = 0


class ManifestRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')
    entry: str = Field(default="index.html")
    description: str = ""
    author: str = ""
    dimension: Optional[DimensionThemeRequest] = None
    permissions: List[str] = []
    credits: Optional[CreditsRequest] = None
    tags: List[str] = []


class RegisterAppRequest(BaseModel):
    manifest: ManifestRequest
    sourceBase64: str = Field(..., description="Base64 encoded source ZIP")


class RegisterAppResponse(BaseModel):
    success: bool
    appId: Optional[str] = None
    error: Optional[str] = None
    sandboxUrl: Optional[str] = None


class AppListItem(BaseModel):
    appId: str
    name: str
    version: str
    status: str
    createdAt: str
    updatedAt: str
    createdBy: str


class AppListResponse(BaseModel):
    apps: List[AppListItem]
    total: int
    limit: int
    offset: int


class AppDetailResponse(BaseModel):
    appId: str
    manifest: dict
    status: str
    currentVersion: str
    versions: List[dict]
    createdAt: str
    updatedAt: str
    createdBy: str
    sandboxUrl: str


class UpdateStatusRequest(BaseModel):
    status: str = Field(..., description="new status: active, inactive, rejected")


class ValidationResult(BaseModel):
    valid: bool
    errors: List[str]
    warnings: List[str]


class BuildResponse(BaseModel):
    success: bool
    error: Optional[str] = None


# ============================================
# Dependencies
# ============================================

async def require_admin(
    user_id: str = Depends(require_user_id),
    is_admin: bool = Depends(get_is_admin),
) -> str:
    """Admin 권한 필수"""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


def get_registry() -> AppRegistryService:
    """레지스트리 서비스"""
    return get_app_registry()


# ============================================
# Endpoints
# ============================================

@router.post("/apps/validate", response_model=ValidationResult)
async def validate_manifest(
    manifest: ManifestRequest,
    _user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """매니페스트 검증"""
    manifest_dict = manifest.model_dump()
    valid, errors, warnings = registry.validate_manifest(manifest_dict)
    return ValidationResult(valid=valid, errors=errors, warnings=warnings)


@router.post("/apps/register", response_model=RegisterAppResponse)
async def register_app(
    request: RegisterAppRequest,
    user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """앱 등록"""
    try:
        # Decode source
        source_content = base64.b64decode(request.sourceBase64)
    except Exception:
        return RegisterAppResponse(success=False, error="Invalid base64 source")
    
    # Convert manifest to dict
    manifest_dict = request.manifest.model_dump()
    
    # Register
    success, app, error = await registry.register_app(
        manifest_data=manifest_dict,
        source_content=source_content,
        user_id=user_id,
    )
    
    if not success:
        return RegisterAppResponse(success=False, error=error)
    
    return RegisterAppResponse(
        success=True,
        appId=app.app_id,
        sandboxUrl=app.sandbox_url,
    )


@router.post("/apps/register/file", response_model=RegisterAppResponse)
async def register_app_with_file(
    file: UploadFile = File(...),
    manifest_json: str = Form(...),
    user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """파일 업로드로 앱 등록"""
    import json
    
    try:
        manifest_dict = json.loads(manifest_json)
    except json.JSONDecodeError:
        return RegisterAppResponse(success=False, error="Invalid manifest JSON")
    
    # Read file
    source_content = await file.read()
    
    # Register
    success, app, error = await registry.register_app(
        manifest_data=manifest_dict,
        source_content=source_content,
        user_id=user_id,
    )
    
    if not success:
        return RegisterAppResponse(success=False, error=error)
    
    return RegisterAppResponse(
        success=True,
        appId=app.app_id,
        sandboxUrl=app.sandbox_url,
    )


@router.post("/apps/{app_id}/build", response_model=BuildResponse)
async def build_app(
    app_id: str,
    _user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """앱 빌드 (난독화 + SDK 주입)"""
    success, error = await registry.build_app(app_id)
    return BuildResponse(success=success, error=error)


@router.get("/apps", response_model=AppListResponse)
async def list_apps(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """앱 목록"""
    app_status = None
    if status:
        try:
            app_status = AppStatus(status)
        except ValueError:
            pass
    
    apps, total = registry.list_apps(status=app_status, limit=limit, offset=offset)
    
    return AppListResponse(
        apps=[
            AppListItem(
                appId=app.app_id,
                name=app.manifest.name,
                version=app.current_version,
                status=app.status.value,
                createdAt=app.created_at,
                updatedAt=app.updated_at,
                createdBy=app.created_by,
            )
            for app in apps
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/apps/{app_id}", response_model=AppDetailResponse)
async def get_app(
    app_id: str,
    _user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """앱 상세"""
    app = registry.get_app(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    data = app.to_dict()
    return AppDetailResponse(
        appId=data["appId"],
        manifest=data["manifest"],
        status=data["status"],
        currentVersion=data["currentVersion"],
        versions=data["versions"],
        createdAt=data["createdAt"],
        updatedAt=data["updatedAt"],
        createdBy=data["createdBy"],
        sandboxUrl=data["sandboxUrl"],
    )


@router.patch("/apps/{app_id}/status", response_model=BuildResponse)
async def update_app_status(
    app_id: str,
    request: UpdateStatusRequest,
    _user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """앱 상태 변경"""
    try:
        status = AppStatus(request.status)
    except ValueError:
        return BuildResponse(success=False, error=f"Invalid status: {request.status}")
    
    success = registry.update_status(app_id, status)
    if not success:
        return BuildResponse(success=False, error="App not found")
    
    return BuildResponse(success=True)


@router.delete("/apps/{app_id}", response_model=BuildResponse)
async def delete_app(
    app_id: str,
    _user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """앱 삭제"""
    success = registry.delete_app(app_id)
    if not success:
        return BuildResponse(success=False, error="App not found")
    
    return BuildResponse(success=True)


@router.get("/apps/{app_id}/preview-url")
async def get_preview_url(
    app_id: str,
    _user_id: str = Depends(require_admin),
    registry: AppRegistryService = Depends(get_registry),
):
    """미리보기 URL 생성"""
    app = registry.get_app(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    # Generate preview token (in production: signed token with expiry)
    import secrets
    preview_token = secrets.token_urlsafe(32)
    
    return {
        "previewUrl": f"/sandbox/{app_id}?preview={preview_token}",
        "expiresIn": 3600,  # 1 hour
    }


# ============================================
# Tool Registry (Dynamic)
# ============================================

from app.models import Tool, ToolSchema
from app.schemas.tools import ToolRegistration, ToolResponse
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.tool_loader import DynamicToolLoader
from sqlalchemy import select

@router.post("/tools/register", response_model=ToolResponse)
async def register_tool(
    tool_in: ToolRegistration,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new tool dynamically.
    
    Creates a new Tool record and initial v1.0.0 schema.
    Invalidates the tool cache to allow immediate usage.
    """
    # Check if exists
    stmt = select(Tool).where(Tool.tool_key == tool_in.tool_key)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Tool key '{tool_in.tool_key}' already exists")
    
    # Create Tool
    new_tool = Tool(
        tool_key=tool_in.tool_key,
        dimension=tool_in.dimension,
        category=tool_in.category,
        name_ko=tool_in.name_ko,
        name_en=tool_in.name_en,
        description_ko=tool_in.description_ko,
        description_en=tool_in.description_en,
        endpoint=tool_in.endpoint,
        executor_type=tool_in.executor_type,
        timeout_seconds=tool_in.timeout_seconds,
        credit_cost=tool_in.credit_cost,
        billing_type=tool_in.billing_type,
        color=tool_in.color,
        icon=tool_in.icon,
        is_active=True,
    )
    db.add(new_tool)
    await db.flush()  # get ID for schema
    
    # Create Schema (v1.0.0)
    new_schema = ToolSchema(
        tool_id=new_tool.id,
        version="v1.0.0",
        input_schema=tool_in.input_schema,
        output_schema=tool_in.output_schema,
        is_current=True,
    )
    db.add(new_schema)
    
    try:
        await db.commit()
        await db.refresh(new_tool)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "Create tool"))
    
    # Invalidate Cache
    loader = DynamicToolLoader(db)
    await loader.invalidate_cache()
    
    return new_tool


# ============================================
# Settlement Management
# ============================================

from app.services.fork_revenue_service import (
    process_batch_settlements,
    get_settlement_by_id,
    process_settlement,
)
from app.models_settlement import SettlementTransaction, SettlementStatus


class SettlementListItem(BaseModel):
    """Settlement list item."""
    id: str
    tool_key: str
    status: str
    total_credits: int
    platform_fee: int
    creator_pool: int
    payer_user_id: Optional[str]
    created_at: str
    processed_at: Optional[str]
    error_message: Optional[str]


class SettlementListResponse(BaseModel):
    """Settlement list response."""
    settlements: List[SettlementListItem]
    total: int
    pending_count: int
    failed_count: int


class BatchProcessRequest(BaseModel):
    """Batch process request."""
    limit: int = Field(default=100, ge=1, le=500)


class BatchProcessResponse(BaseModel):
    """Batch process response."""
    processed: int
    succeeded: int
    failed: int
    errors: List[dict]


@router.get("/settlements/pending", response_model=SettlementListResponse)
async def list_pending_settlements(
    limit: int = 50,
    offset: int = 0,
    _user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List pending settlements."""
    from sqlalchemy import select, func
    
    # Validate inputs
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    
    try:
        # Get pending settlements
        query = (
            select(SettlementTransaction)
            .where(SettlementTransaction.status == SettlementStatus.PENDING.value)
            .order_by(SettlementTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        settlements = result.scalars().all()
        
        # Get counts
        pending_count = await db.execute(
            select(func.count(SettlementTransaction.id))
            .where(SettlementTransaction.status == SettlementStatus.PENDING.value)
        )
        failed_count = await db.execute(
            select(func.count(SettlementTransaction.id))
            .where(SettlementTransaction.status == SettlementStatus.FAILED.value)
        )
        total_count = await db.execute(
            select(func.count(SettlementTransaction.id))
        )
        
        return SettlementListResponse(
            settlements=[
                SettlementListItem(
                    id=str(s.id),
                    tool_key=s.tool_key or "unknown",
                    status=s.status or "unknown",
                    total_credits=s.total_credits or 0,
                    platform_fee=s.platform_fee or 0,
                    creator_pool=s.creator_pool or 0,
                    payer_user_id=s.payer_user_id,
                    created_at=s.created_at.isoformat() if s.created_at else "",
                    processed_at=s.processed_at.isoformat() if s.processed_at else None,
                    error_message=(s.error_message or "")[:200] if s.error_message else None,
                )
                for s in settlements
            ],
            total=total_count.scalar() or 0,
            pending_count=pending_count.scalar() or 0,
            failed_count=failed_count.scalar() or 0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "Database operation"))


@router.get("/settlements/failed", response_model=SettlementListResponse)
async def list_failed_settlements(
    limit: int = 50,
    offset: int = 0,
    _user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List failed settlements."""
    from sqlalchemy import select, func
    
    query = (
        select(SettlementTransaction)
        .where(SettlementTransaction.status == SettlementStatus.FAILED.value)
        .order_by(SettlementTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    settlements = result.scalars().all()
    
    pending_count = await db.execute(
        select(func.count(SettlementTransaction.id))
        .where(SettlementTransaction.status == SettlementStatus.PENDING.value)
    )
    failed_count = await db.execute(
        select(func.count(SettlementTransaction.id))
        .where(SettlementTransaction.status == SettlementStatus.FAILED.value)
    )
    total_count = await db.execute(
        select(func.count(SettlementTransaction.id))
    )
    
    return SettlementListResponse(
        settlements=[
            SettlementListItem(
                id=str(s.id),
                tool_key=s.tool_key,
                status=s.status,
                total_credits=s.total_credits,
                platform_fee=s.platform_fee,
                creator_pool=s.creator_pool,
                payer_user_id=s.payer_user_id,
                created_at=s.created_at.isoformat() if s.created_at else "",
                processed_at=s.processed_at.isoformat() if s.processed_at else None,
                error_message=s.error_message,
            )
            for s in settlements
        ],
        total=total_count.scalar() or 0,
        pending_count=pending_count.scalar() or 0,
        failed_count=failed_count.scalar() or 0,
    )


@router.post("/settlements/process-batch", response_model=BatchProcessResponse)
async def trigger_batch_settlement(
    request: BatchProcessRequest = BatchProcessRequest(),
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger batch settlement processing."""
    result = await process_batch_settlements(
        db=db,
        limit=request.limit,
        processed_by=user_id,
    )
    
    return BatchProcessResponse(
        processed=result["processed"],
        succeeded=result["succeeded"],
        failed=result["failed"],
        errors=result["errors"],
    )


@router.post("/settlements/{settlement_id}/retry")
async def retry_settlement(
    settlement_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retry a specific failed settlement."""
    from uuid import UUID
    
    try:
        sid = UUID(settlement_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid settlement ID")
    
    settlement = await get_settlement_by_id(db, sid)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    if settlement.status == SettlementStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Settlement already completed")
    
    # Reset to pending for retry
    settlement.status = SettlementStatus.PENDING.value
    settlement.error_message = None
    await db.commit()
    
    # Process
    success, error = await process_settlement(db, sid, processed_by=user_id)
    
    return {
        "success": success,
        "error": error,
        "settlement_id": settlement_id,
    }


# ============================================
# Dead Letter Queue (DLQ) Management
# ============================================

from app.services.dlq_service import (
    list_dlq_items,
    get_dlq_item,
    get_dlq_stats,
    retry_dlq_item,
    resolve_dlq_item,
)
from app.models_dlq import DLQStatus, DLQEventType


class DLQItemResponse(BaseModel):
    """DLQ item response."""
    id: str
    event_type: str
    status: str
    user_id: str
    operation_type: str
    amount: int
    error_message: str
    retry_count: int
    created_at: str
    resolved_by: Optional[str]
    resolved_at: Optional[str]


class DLQListResponse(BaseModel):
    """DLQ list response."""
    items: List[DLQItemResponse]
    total: int


class DLQStatsResponse(BaseModel):
    """DLQ statistics response."""
    by_status: dict
    pending_by_type: dict
    pending_refund_credits: int
    total_pending: int


class DLQResolveRequest(BaseModel):
    """DLQ resolve request."""
    resolution_notes: str = Field(..., min_length=1, max_length=500)
    skip: bool = Field(default=False, description="Mark as skipped instead of resolved")


@router.get("/dlq", response_model=DLQListResponse)
async def list_dlq(
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List DLQ items with optional filters."""
    try:
        dlq_status = DLQStatus(status) if status else None
    except ValueError:
        dlq_status = None
    
    try:
        dlq_event_type = DLQEventType(event_type) if event_type else None
    except ValueError:
        dlq_event_type = None
    
    items, total = await list_dlq_items(
        db=db,
        status=dlq_status,
        event_type=dlq_event_type,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    
    return DLQListResponse(
        items=[
            DLQItemResponse(
                id=str(item.id),
                event_type=item.event_type,
                status=item.status,
                user_id=item.user_id,
                operation_type=item.operation_type,
                amount=item.amount,
                error_message=item.error_message[:200],
                retry_count=item.retry_count,
                created_at=item.created_at.isoformat() if item.created_at else "",
                resolved_by=item.resolved_by,
                resolved_at=item.resolved_at.isoformat() if item.resolved_at else None,
            )
            for item in items
        ],
        total=total,
    )


@router.get("/dlq/stats", response_model=DLQStatsResponse)
async def get_dlq_statistics(
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get DLQ statistics for admin dashboard."""
    stats = await get_dlq_stats(db)
    return DLQStatsResponse(**stats)


@router.post("/dlq/{item_id}/retry")
async def retry_dlq(
    item_id: str,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retry processing a DLQ item (e.g., retry a failed refund)."""
    from uuid import UUID
    
    try:
        iid = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    success, error = await retry_dlq_item(db, iid, processed_by=admin_id)
    
    return {
        "success": success,
        "error": error,
        "item_id": item_id,
    }


@router.post("/dlq/{item_id}/resolve")
async def resolve_dlq(
    item_id: str,
    request: DLQResolveRequest,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually resolve a DLQ item."""
    from uuid import UUID
    
    try:
        iid = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    success, error = await resolve_dlq_item(
        db=db,
        item_id=iid,
        resolved_by=admin_id,
        resolution_notes=request.resolution_notes,
        skip=request.skip,
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "item_id": item_id,
        "status": "skipped" if request.skip else "resolved",
    }


# ============================================
# Circuit Breaker Management
# ============================================

from app.services.circuit_breaker import CircuitBreaker


# ============================================
# Academy Account Linking (수강생 계정 연결)
# ============================================

from app.models import CrebitApplication, UserAccount


class LinkAccountRequest(BaseModel):
    """Academy 계정 연결 요청."""
    name: str = Field(..., min_length=1, max_length=100, description="수강 신청서에 적은 이름")
    google_email: str = Field(..., min_length=5, max_length=255, description="Google 로그인 이메일")


class LinkAccountResponse(BaseModel):
    """Academy 계정 연결 응답."""
    success: bool
    application_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str


@router.post("/academy/link", response_model=LinkAccountResponse)
async def link_academy_account(
    request: LinkAccountRequest,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """관리자: 수강 신청에 Google 계정 연결

    오프라인 결제 수강생의 Google 이메일을 crebit_applications.owner_id에 연결합니다.

    사용 흐름:
    1. 수강생이 crebit.studio에서 Google 로그인
    2. /academy 접속 → "수강생 전용" 표시
    3. 카톡에 "이름 / Google이메일" 댓글
    4. 관리자가 이 API로 연결
    5. 수강생 /academy 접속 가능

    Args:
        name: 수강 신청서에 적은 이름 (부분 일치 지원)
        google_email: 로그인용 Google 이메일
    """
    # 1. name으로 crebit_applications 찾기 (status=paid)
    # 1차: 정확 매칭
    app_query = (
        select(CrebitApplication)
        .where(CrebitApplication.name == request.name)
        .where(CrebitApplication.status == "paid")
    )
    result = await db.execute(app_query)
    application = result.scalar_one_or_none()

    # 2차: 정확 매칭 실패시 부분 매칭 + 후보 제시
    if not application:
        # 공백 제거 후 부분 매칭
        name_clean = request.name.strip().replace(" ", "")
        fuzzy_query = (
            select(CrebitApplication)
            .where(CrebitApplication.status == "paid")
            .where(CrebitApplication.owner_id.is_(None))  # 미연결만
        )
        fuzzy_result = await db.execute(fuzzy_query)
        all_paid = fuzzy_result.scalars().all()
        
        # 부분 매칭 찾기
        candidates = []
        for app in all_paid:
            app_name_clean = app.name.replace(" ", "")
            if name_clean in app_name_clean or app_name_clean in name_clean:
                application = app  # 부분 매칭 성공
                break
            # 후보 목록 (비슷한 이름)
            if len(candidates) < 5:
                candidates.append(app.name)
        
        if not application:
            if candidates:
                return LinkAccountResponse(
                    success=False,
                    message=f"'{request.name}' 미발견. 비슷한 이름: {', '.join(candidates)}"
                )
            return LinkAccountResponse(
                success=False,
                message=f"결제 완료된 수강 신청을 찾을 수 없습니다: '{request.name}'"
            )

    # 이미 연결된 경우 확인
    if application.owner_id:
        return LinkAccountResponse(
            success=False,
            application_id=str(application.id),
            user_id=application.owner_id,
            message=f"이미 다른 계정에 연결되어 있습니다: {application.owner_id}"
        )

    # 2. google_email로 user_accounts에서 user_id 찾기
    email_lower = request.google_email.strip().lower()
    user_query = (
        select(UserAccount)
        .where(UserAccount.email == email_lower)
    )
    result = await db.execute(user_query)
    user_account = result.scalar_one_or_none()

    if not user_account:
        return LinkAccountResponse(
            success=False,
            application_id=str(application.id),
            message=f"해당 이메일로 로그인한 기록이 없습니다: '{request.google_email}'. 수강생이 먼저 crebit.studio에서 Google 로그인 해야 합니다."
        )

    # 3. application.owner_id = user_id 설정
    application.owner_id = user_account.user_id

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "Link account"))

    return LinkAccountResponse(
        success=True,
        application_id=str(application.id),
        user_id=user_account.user_id,
        message=f"계정 연결 완료: {request.name} → {request.google_email}"
    )


@router.get("/academy/applications")
async def list_academy_applications(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """관리자: 수강 신청 목록 조회

    status 필터: pending, paid, cancelled, refunded
    """
    from sqlalchemy import func

    query = select(CrebitApplication).order_by(CrebitApplication.id.desc())

    if status:
        query = query.where(CrebitApplication.status == status)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    applications = result.scalars().all()

    # 총 개수
    count_query = select(func.count(CrebitApplication.id))
    if status:
        count_query = count_query.where(CrebitApplication.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return {
        "applications": [
            {
                "id": str(app.id),
                "name": app.name,
                "email": app.email,
                "phone": app.phone,
                "track": app.track,
                "status": app.status,
                "owner_id": app.owner_id,
                "paid_amount": app.paid_amount,
                "paid_at": app.paid_at.isoformat() if app.paid_at else None,
            }
            for app in applications
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


class ActivateStudentRequest(BaseModel):
    """수강생 활성화 요청 (Gmail만 입력)."""
    google_email: str = Field(..., min_length=5, max_length=255, description="수강생 Google 이메일")
    name: str = Field(default="", max_length=100, description="수강생 이름 (선택)")
    cohort: str = Field(default="1기", max_length=50, description="기수")


class ActivateStudentResponse(BaseModel):
    """수강생 활성화 응답."""
    success: bool
    application_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str
    already_exists: bool = False


@router.post("/academy/activate", response_model=ActivateStudentResponse)
async def activate_academy_student(
    request: ActivateStudentRequest,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """관리자: Gmail만 입력하면 수강생 즉시 활성화

    1. 해당 Gmail로 로그인한 user_accounts 찾기
    2. 없으면 에러 (먼저 Google 로그인 필요)
    3. 이미 paid 수강신청 있으면 그대로 반환
    4. 없으면 새 수강신청 생성 (status=paid)
    """
    import uuid
    from datetime import datetime

    email_lower = request.google_email.strip().lower()

    # 1. user_accounts에서 user_id 찾기
    user_query = select(UserAccount).where(UserAccount.email == email_lower)
    user_result = await db.execute(user_query)
    user_account = user_result.scalar_one_or_none()

    if not user_account:
        # Pre-Activation: 로그인 전이라도 미리 활성화 - 나중에 로그인 시 자동 매칭됨 (auth.py)
        existing_unlinked = await db.execute(
            select(CrebitApplication)
            .where(CrebitApplication.email == email_lower)
            .where(CrebitApplication.status == "paid")
        )
        if existing_unlinked.scalar_one_or_none():
            return ActivateStudentResponse(
                success=True,
                message=f"이미 사전 활성화된 수강생입니다 (로그인 대기 중): {email_lower}",
                already_exists=True,
            )

        new_app = CrebitApplication(
            id=uuid.uuid4(),
            name=request.name or email_lower.split("@")[0],
            email=email_lower,
            phone="",
            track="A",
            status="paid",
            cohort=request.cohort,
            owner_id=None,  # 로그인 시 자동 매칭
            paid_at=datetime.utcnow(),
            paid_amount=0,
        )
        db.add(new_app)
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"사전 활성화 실패: {str(e)}")

        return ActivateStudentResponse(
            success=True,
            application_id=str(new_app.id),
            user_id=None,
            message=f"사전 활성화 완료 (로그인 대기 중): {new_app.name}. 학생이 Google 로그인하면 자동 연결됩니다."
        )

    # 2. 이미 paid 수강신청 있는지 확인
    app_query = (
        select(CrebitApplication)
        .where(CrebitApplication.owner_id == user_account.user_id)
        .where(CrebitApplication.status == "paid")
    )
    app_result = await db.execute(app_query)
    existing_app = app_result.scalar_one_or_none()

    if existing_app:
        return ActivateStudentResponse(
            success=True,
            application_id=str(existing_app.id),
            user_id=user_account.user_id,
            message=f"이미 활성화된 수강생입니다: {existing_app.name} ({existing_app.cohort})",
            already_exists=True
        )

    # 3. 새 수강신청 생성
    new_app = CrebitApplication(
        id=uuid.uuid4(),
        name=request.name or email_lower.split("@")[0],
        email=email_lower,
        phone="",
        track="A",
        status="paid",
        cohort=request.cohort,
        owner_id=user_account.user_id,
        paid_at=datetime.utcnow(),
        paid_amount=0,
    )
    db.add(new_app)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"수강생 활성화 실패: {str(e)}")

    return ActivateStudentResponse(
        success=True,
        application_id=str(new_app.id),
        user_id=user_account.user_id,
        message=f"수강생 활성화 완료: {new_app.name} ({request.cohort})"
    )


# --- Bulk Activation ---

class BulkActivateRequest(BaseModel):
    """여러 Gmail 한번에 활성화"""
    emails: list[str]  # 최대 20개
    cohort: str = "1기"


class BulkActivateResult(BaseModel):
    email: str
    success: bool
    message: str


class BulkActivateResponse(BaseModel):
    total: int
    success_count: int
    fail_count: int
    results: list[BulkActivateResult]


@router.post("/academy/activate-bulk", response_model=BulkActivateResponse)
async def bulk_activate_academy_students(
    request: BulkActivateRequest,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """관리자: 여러 Gmail 한번에 활성화 (최대 20개)"""
    import uuid
    from datetime import datetime

    # 최대 20개 제한
    emails = request.emails[:20]
    results: list[BulkActivateResult] = []
    success_count = 0

    for email_raw in emails:
        email = email_raw.strip().lower()
        if not email:
            continue

        # 1. user_accounts에서 user_id 찾기
        user_query = select(UserAccount).where(UserAccount.email == email)
        user_result = await db.execute(user_query)
        user_account = user_result.scalar_one_or_none()

        if not user_account:
            # Pre-Activation: 로그인 전이라도 미리 활성화
            existing_unlinked = await db.execute(
                select(CrebitApplication)
                .where(CrebitApplication.email == email)
                .where(CrebitApplication.status == "paid")
            )
            if existing_unlinked.scalar_one_or_none():
                results.append(BulkActivateResult(
                    email=email,
                    success=True,
                    message="이미 사전 활성화됨 (로그인 대기)"
                ))
                success_count += 1
                continue

            new_app = CrebitApplication(
                id=uuid.uuid4(),
                name=email.split("@")[0],
                email=email,
                phone="",
                track="A",
                status="paid",
                cohort=request.cohort,
                owner_id=None,  # 로그인 시 자동 매칭
                paid_at=datetime.utcnow(),
                paid_amount=0,
            )
            db.add(new_app)
            results.append(BulkActivateResult(
                email=email,
                success=True,
                message="사전 활성화 완료 (로그인 대기)"
            ))
            success_count += 1
            continue

        # 2. 이미 paid 수강신청 있는지 확인
        app_query = (
            select(CrebitApplication)
            .where(CrebitApplication.owner_id == user_account.user_id)
            .where(CrebitApplication.status == "paid")
        )
        app_result = await db.execute(app_query)
        existing_app = app_result.scalar_one_or_none()

        if existing_app:
            results.append(BulkActivateResult(
                email=email,
                success=True,
                message="이미 활성화됨"
            ))
            success_count += 1
            continue

        # 3. 새 수강신청 생성
        new_app = CrebitApplication(
            id=uuid.uuid4(),
            name=email.split("@")[0],
            email=email,
            phone="",
            track="A",
            status="paid",
            cohort=request.cohort,
            owner_id=user_account.user_id,
            paid_at=datetime.utcnow(),
            paid_amount=0,
        )
        db.add(new_app)
        results.append(BulkActivateResult(
            email=email,
            success=True,
            message="활성화 완료"
        ))
        success_count += 1

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"벌크 활성화 실패: {str(e)}")

    return BulkActivateResponse(
        total=len(results),
        success_count=success_count,
        fail_count=len(results) - success_count,
        results=results
    )

class DeactivateStudentRequest(BaseModel):
    """수강생 비활성화 요청."""
    email: str = Field(..., min_length=5, max_length=255, description="비활성화할 수강생 이메일")


class DeactivateStudentResponse(BaseModel):
    """수강생 비활성화 응답."""
    success: bool
    message: str
    deactivated: dict


@router.post("/academy/deactivate", response_model=DeactivateStudentResponse)
async def deactivate_academy_student(
    request: DeactivateStudentRequest,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """관리자: 수강생 권한 비활성화

    1. CrebitApplication.status → "cancelled", owner_id → None
    2. AccessRequest.status → "rejected"
    """
    from app.models import AccessRequest

    email_lower = request.email.strip().lower()
    deactivated = {"application": False, "access_request": False}

    # 1. CrebitApplication 비활성화 (이메일 또는 owner_id로 찾기)
    # 먼저 이메일로 찾기
    app_query = (
        select(CrebitApplication)
        .where(CrebitApplication.email == email_lower)
        .where(CrebitApplication.status == "paid")
    )
    app_result = await db.execute(app_query)
    application = app_result.scalar_one_or_none()

    # 이메일로 못 찾으면 UserAccount → user_id → CrebitApplication
    if not application:
        user_query = select(UserAccount).where(UserAccount.email == email_lower)
        user_result = await db.execute(user_query)
        user_account = user_result.scalar_one_or_none()

        if user_account:
            app_query2 = (
                select(CrebitApplication)
                .where(CrebitApplication.owner_id == user_account.user_id)
                .where(CrebitApplication.status == "paid")
            )
            app_result2 = await db.execute(app_query2)
            application = app_result2.scalar_one_or_none()

    if application:
        application.status = "cancelled"
        application.owner_id = None
        application.notes = f"관리자({admin_id})에 의해 비활성화됨"
        deactivated["application"] = True

    # 2. AccessRequest 비활성화 (이메일로 찾기)
    ar_query = (
        select(AccessRequest)
        .where(AccessRequest.email == email_lower)
        .where(AccessRequest.status == "approved")
    )
    ar_result = await db.execute(ar_query)
    access_request = ar_result.scalar_one_or_none()

    if access_request:
        access_request.status = "rejected"
        access_request.admin_notes = f"관리자({admin_id})에 의해 승인 취소됨"
        deactivated["access_request"] = True

    if not deactivated["application"] and not deactivated["access_request"]:
        return DeactivateStudentResponse(
            success=False,
            message=f"해당 이메일({email_lower})의 활성화된 수강 기록을 찾을 수 없습니다.",
            deactivated=deactivated,
        )

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"비활성화 실패: {str(e)}")

    return DeactivateStudentResponse(
        success=True,
        message=f"{email_lower} 수강생 비활성화 완료",
        deactivated=deactivated,
    )


@router.get("/circuit-breakers")
async def list_circuit_breakers(
    _admin: str = Depends(require_admin),
):
    """Get status of all circuit breakers."""
    return CircuitBreaker.get_all_status()


@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(
    name: str,
    admin_id: str = Depends(require_admin),
):
    """Reset a circuit breaker to closed state."""
    try:
        CircuitBreaker.reset(name)
        return {
            "success": True,
            "name": name,
            "message": f"Circuit breaker '{name}' reset to CLOSED by {admin_id}",
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")
