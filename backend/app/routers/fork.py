"""Fork API Router.

Endpoints for fork creation, version management, and diff preview.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.utils.error_sanitize import safe_error_detail
from app.models_telemetry import ToolManifest
from app.models_versioning import ToolVersion, ToolDiff, ToolTestCase, VersionStatus
from app.schemas.versioning_schemas import (
    VersionResponse,
    VersionCreate,
    DiffPreview,
    DiffStats,
    DiffResponse,
    ForkCreate,
    ForkPreviewRequest,
    ForkResult,
    TestCaseCreate,
    TestCaseResponse,
)
from app.services import versioning_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fork", tags=["Fork"])


# =============================================================================
# Version Endpoints
# =============================================================================

@router.get("/tools/{tool_id}/versions", response_model=list[VersionResponse])
async def list_versions(
    tool_id: UUID,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all versions of a tool."""
    query = select(ToolVersion).where(ToolVersion.tool_id == tool_id)
    
    if status:
        query = query.where(ToolVersion.status == status)
    
    query = query.order_by(ToolVersion.version_number.desc())
    
    result = await db.execute(query)
    versions = result.scalars().all()
    
    return [VersionResponse.model_validate(v) for v in versions]


@router.get("/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific version."""
    version = await db.get(ToolVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return VersionResponse.model_validate(version)


@router.post("/tools/{tool_id}/versions", response_model=VersionResponse)
async def create_version(
    tool_id: UUID,
    data: VersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new version for a tool you own."""
    # Check tool ownership
    tool = await db.get(ToolManifest, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if tool.created_by != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not tool owner")
    
    version = await versioning_service.create_version(
        db=db,
        tool_id=tool_id,
        code_type=data.code_type,
        code_content=data.code_content,
        created_by=current_user["id"],
        system_prompt=data.system_prompt,
        input_schema=data.input_schema,
        output_schema=data.output_schema,
        dependencies=data.dependencies,
        config=data.config,
        changelog=data.changelog,
    )
    
    return VersionResponse.model_validate(version)


@router.post("/versions/{version_id}/submit")
async def submit_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit a draft version for review."""
    version = await db.get(ToolVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    if version.created_by != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not version owner")
    
    try:
        updated = await versioning_service.submit_for_review(db, version_id)
        return {"status": "submitted", "version_id": str(updated.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Fork operation"))


@router.post("/versions/{version_id}/approve")
async def approve_version(
    version_id: UUID,
    review_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Approve a version (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        version = await versioning_service.approve_version(
            db=db,
            version_id=version_id,
            reviewed_by=current_user["id"],
            review_notes=review_notes,
        )
        return {"status": "approved", "version_id": str(version.id), "is_live": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Fork operation"))


# =============================================================================
# Diff & Fork Endpoints
# =============================================================================

@router.post("/tools/{tool_id}/preview-diff", response_model=DiffPreview)
async def preview_diff(
    tool_id: UUID,
    data: ForkPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Preview diff before creating a fork.
    
    Returns diff statistics and Sybil warning if changes are trivial.
    """
    # Get original live version
    version = await versioning_service.get_live_version(db, tool_id)
    if not version:
        raise HTTPException(status_code=404, detail="Tool has no live version")
    
    # Compute diff
    diff_stats = versioning_service.compute_diff(version.code_content, data.code_content)
    semantic = versioning_service.analyze_semantic_changes(
        version.code_content,
        data.code_content,
        version.code_type,
    )
    score, is_trivial = versioning_service.calculate_attribution_score(
        diff_stats,
        semantic,
        len(version.code_content),
    )
    
    sybil_warning = None
    if is_trivial:
        sybil_warning = (
            "⚠️ Warning: These changes appear trivial and may be flagged as Sybil attack. "
            "Trivial forks receive minimal revenue share. "
            "Consider making more significant improvements."
        )
    
    return DiffPreview(
        diff_content=diff_stats["diff_content"],
        stats=DiffStats(
            lines_added=diff_stats["lines_added"],
            lines_removed=diff_stats["lines_removed"],
            lines_modified=diff_stats["lines_modified"],
            similarity_ratio=diff_stats["similarity_ratio"],
            diff_score=score,
            is_trivial=is_trivial,
        ),
        semantic_changes=semantic,
        sybil_warning=sybil_warning,
    )


@router.post("/tools/{tool_id}/fork", response_model=ForkResult)
async def create_fork(
    tool_id: UUID,
    data: ForkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a fork of a tool.
    
    1. Validates changes
    2. Creates new ToolManifest
    3. Creates ToolVersion with forked code
    4. Creates ForkEvent with attribution score
    5. Creates ToolDiff for tracking
    
    The fork starts in pending_review status.
    """
    # Check tool key uniqueness
    existing = await db.execute(
        select(ToolManifest).where(ToolManifest.tool_key == data.new_tool_key)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Tool key already exists")
    
    try:
        tool, version, diff = await versioning_service.create_fork_with_diff(
            db=db,
            original_tool_id=tool_id,
            forked_code=data.code_content,
            forked_by=current_user["id"],
            new_tool_key=data.new_tool_key,
            new_display_name=data.new_display_name,
            changelog=data.changelog,
            code_type=data.code_type,
        )
        
        # Copy test cases
        await versioning_service.copy_test_cases_to_fork(
            db, tool_id, tool.id, current_user["id"]
        )
        
        return ForkResult(
            tool_id=tool.id,
            tool_key=tool.tool_key,
            version_id=version.id,
            fork_event_id=diff.fork_event_id,
            diff=DiffStats(
                lines_added=diff.lines_added,
                lines_removed=diff.lines_removed,
                lines_modified=diff.lines_modified,
                similarity_ratio=diff.similarity_ratio,
                diff_score=diff.diff_score,
                is_trivial=diff.is_trivial_change,
            ),
            needs_review=True,
            sybil_flagged=diff.is_trivial_change,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Fork operation"))


@router.get("/diffs/{diff_id}", response_model=DiffResponse)
async def get_diff(
    diff_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get diff details."""
    diff = await db.get(ToolDiff, diff_id)
    if not diff:
        raise HTTPException(status_code=404, detail="Diff not found")
    
    return DiffResponse.model_validate(diff)


# =============================================================================
# Test Case Endpoints
# =============================================================================

@router.get("/tools/{tool_id}/tests", response_model=list[TestCaseResponse])
async def list_test_cases(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List test cases for a tool."""
    result = await db.execute(
        select(ToolTestCase)
        .where(ToolTestCase.tool_id == tool_id)
        .where(ToolTestCase.is_active == True)
    )
    tests = result.scalars().all()
    
    return [TestCaseResponse.model_validate(t) for t in tests]


@router.post("/tools/{tool_id}/tests", response_model=TestCaseResponse)
async def create_test_case(
    tool_id: UUID,
    data: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a test case for a tool you own."""
    tool = await db.get(ToolManifest, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if tool.created_by != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not tool owner")
    
    from uuid import uuid4
    from datetime import datetime
    
    test = ToolTestCase(
        id=uuid4(),
        tool_id=tool_id,
        name=data.name,
        description=data.description,
        input_data=data.input_data,
        expected_output=data.expected_output,
        validation_rules=data.validation_rules or {},
        is_required=data.is_required,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user["id"],
    )
    
    db.add(test)
    await db.commit()
    await db.refresh(test)
    
    return TestCaseResponse.model_validate(test)
