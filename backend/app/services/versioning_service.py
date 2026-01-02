"""Tool Version and Diff Service.

Handles:
- Version creation and management
- Diff calculation with attribution scoring
- Sybil detection for trivial forks
- Test case management
"""
import difflib
import re
import logging
from datetime import datetime
from typing import Optional, Tuple, List
from uuid import UUID, uuid4

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_telemetry import ToolManifest, ForkEvent
from app.models_versioning import (
    ToolVersion,
    ToolDiff,
    ToolTestCase,
    CodeType,
    VersionStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Diff Calculation
# =============================================================================

def compute_diff(original: str, forked: str) -> dict:
    """
    Compute unified diff between two code versions.
    
    Returns:
        {
            "diff_content": str,
            "lines_added": int,
            "lines_removed": int,
            "lines_modified": int,
            "similarity_ratio": float,
        }
    """
    original_lines = original.splitlines(keepends=True)
    forked_lines = forked.splitlines(keepends=True)
    
    # Generate unified diff
    diff = list(difflib.unified_diff(
        original_lines,
        forked_lines,
        fromfile='original',
        tofile='forked',
        lineterm=''
    ))
    diff_content = ''.join(diff)
    
    # Count changes
    lines_added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    lines_removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    
    # Estimate modified (heuristic: min of added/removed changes)
    lines_modified = min(lines_added, lines_removed)
    lines_added -= lines_modified
    lines_removed -= lines_modified
    
    # Calculate similarity
    matcher = difflib.SequenceMatcher(None, original, forked)
    similarity = matcher.ratio()
    
    return {
        "diff_content": diff_content,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "lines_modified": lines_modified,
        "similarity_ratio": round(similarity, 4),
    }


def analyze_semantic_changes(
    original: str,
    forked: str,
    code_type: str,
) -> dict:
    """
    Analyze semantic changes between versions.
    
    For prompt templates, looks for:
    - Changed variables
    - Modified instructions
    - Added/removed sections
    """
    changes = {
        "prompt_modified": False,
        "variables_changed": [],
        "sections_added": [],
        "sections_removed": [],
    }
    
    if code_type == CodeType.PROMPT_TEMPLATE.value:
        # Find variables ({{variable}} or {variable})
        orig_vars = set(re.findall(r'\{\{?(\w+)\}?\}', original))
        fork_vars = set(re.findall(r'\{\{?(\w+)\}?\}', forked))
        
        added_vars = fork_vars - orig_vars
        removed_vars = orig_vars - fork_vars
        
        if added_vars or removed_vars:
            changes["variables_changed"] = list(added_vars | removed_vars)
        
        # Check if core prompt changed (beyond variable substitution)
        # Remove variables and compare
        orig_clean = re.sub(r'\{\{?\w+\}?\}', '', original)
        fork_clean = re.sub(r'\{\{?\w+\}?\}', '', forked)
        
        if difflib.SequenceMatcher(None, orig_clean, fork_clean).ratio() < 0.95:
            changes["prompt_modified"] = True
    
    return changes


def calculate_attribution_score(
    diff_stats: dict,
    semantic_changes: dict,
    original_length: int,
) -> Tuple[int, bool]:
    """
    Calculate attribution score (0-100) based on changes.
    
    Higher score = more original work by fork creator.
    Lower score = mostly copied from original.
    
    Also returns is_trivial (Sybil flag).
    """
    similarity = diff_stats.get("similarity_ratio", 1.0)
    lines_added = diff_stats.get("lines_added", 0)
    lines_modified = diff_stats.get("lines_modified", 0)
    lines_removed = diff_stats.get("lines_removed", 0)
    
    # Total changes
    total_changes = lines_added + lines_modified + lines_removed
    
    # Base score from change ratio
    if original_length > 0:
        change_ratio = total_changes / original_length
    else:
        change_ratio = 1.0 if total_changes > 0 else 0.0
    
    # Score calculation
    # 100% similar = 0 score
    # 0% similar = 100 score
    base_score = (1 - similarity) * 100
    
    # Bonus for semantic changes
    if semantic_changes.get("prompt_modified"):
        base_score += 10
    if semantic_changes.get("variables_changed"):
        base_score += 5 * len(semantic_changes["variables_changed"])
    
    # Cap at 100
    score = min(100, max(0, int(base_score)))
    
    # Sybil detection: trivial change?
    is_trivial = (
        similarity > 0.95 and  # Very similar
        total_changes < 5 and   # Very few changes
        not semantic_changes.get("prompt_modified")  # No real change
    )
    
    return score, is_trivial


# =============================================================================
# Version Management
# =============================================================================

async def create_version(
    db: AsyncSession,
    tool_id: UUID,
    code_type: str,
    code_content: str,
    created_by: str,
    system_prompt: Optional[str] = None,
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
    dependencies: Optional[dict] = None,
    config: Optional[dict] = None,
    changelog: Optional[str] = None,
) -> ToolVersion:
    """Create a new tool version (draft status)."""
    
    # Get next version number
    result = await db.execute(
        select(func.max(ToolVersion.version_number))
        .where(ToolVersion.tool_id == tool_id)
    )
    max_version = result.scalar() or 0
    next_version = max_version + 1
    
    version = ToolVersion(
        id=uuid4(),
        tool_id=tool_id,
        version=f"1.0.{next_version}",
        version_number=next_version,
        code_type=code_type,
        code_content=code_content,
        system_prompt=system_prompt,
        input_schema=input_schema,
        output_schema=output_schema,
        dependencies=dependencies or {},
        config=config or {},
        status=VersionStatus.DRAFT.value,
        is_live=False,
        created_by=created_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        changelog=changelog,
    )
    
    db.add(version)
    await db.commit()
    await db.refresh(version)
    
    logger.info(f"Version created: tool={tool_id}, version={version.version}")
    return version


async def get_live_version(
    db: AsyncSession,
    tool_id: UUID,
) -> Optional[ToolVersion]:
    """Get the current live version of a tool."""
    result = await db.execute(
        select(ToolVersion)
        .where(ToolVersion.tool_id == tool_id)
        .where(ToolVersion.is_live == True)
    )
    return result.scalars().first()


async def submit_for_review(
    db: AsyncSession,
    version_id: UUID,
) -> ToolVersion:
    """Submit a draft version for review."""
    version = await db.get(ToolVersion, version_id)
    if not version:
        raise ValueError("Version not found")
    
    if version.status != VersionStatus.DRAFT.value:
        raise ValueError(f"Cannot submit version with status: {version.status}")
    
    version.status = VersionStatus.PENDING_REVIEW.value
    version.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(version)
    
    return version


async def approve_version(
    db: AsyncSession,
    version_id: UUID,
    reviewed_by: str,
    review_notes: Optional[str] = None,
) -> ToolVersion:
    """Approve a version and make it live."""
    version = await db.get(ToolVersion, version_id)
    if not version:
        raise ValueError("Version not found")
    
    # Demote current live version
    await db.execute(
        update(ToolVersion)
        .where(ToolVersion.tool_id == version.tool_id)
        .where(ToolVersion.is_live == True)
        .values(is_live=False, status=VersionStatus.DEPRECATED.value)
    )
    
    # Approve and make live
    version.status = VersionStatus.APPROVED.value
    version.is_live = True
    version.reviewed_by = reviewed_by
    version.reviewed_at = datetime.utcnow()
    version.review_notes = review_notes
    version.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(version)
    
    logger.info(f"Version approved: {version_id}, by {reviewed_by}")
    return version


# =============================================================================
# Fork with Diff
# =============================================================================

async def create_fork_with_diff(
    db: AsyncSession,
    original_tool_id: UUID,
    forked_code: str,
    forked_by: str,
    new_tool_key: str,
    new_display_name: str,
    changelog: Optional[str] = None,
    code_type: Optional[str] = None,
) -> Tuple[ToolManifest, ToolVersion, ToolDiff]:
    """
    Create a fork with full diff tracking.
    
    1. Get original tool's live version
    2. Create new ToolManifest (forked tool)
    3. Create new ToolVersion with forked code
    4. Calculate diff and attribution score
    5. Create ForkEvent
    6. Create ToolDiff
    
    Returns: (new_tool, new_version, diff)
    """
    # Get original live version
    orig_version = await get_live_version(db, original_tool_id)
    if not orig_version:
        raise ValueError("Original tool has no live version")
    
    original_tool = await db.get(ToolManifest, original_tool_id)
    if not original_tool:
        raise ValueError("Original tool not found")
    
    # Compute diff
    diff_stats = compute_diff(orig_version.code_content, forked_code)
    semantic = analyze_semantic_changes(
        orig_version.code_content,
        forked_code,
        orig_version.code_type,
    )
    attr_score, is_trivial = calculate_attribution_score(
        diff_stats,
        semantic,
        len(orig_version.code_content),
    )
    
    # Create new tool manifest
    new_tool = ToolManifest(
        id=uuid4(),
        tool_key=new_tool_key,
        display_name=new_display_name,
        description=f"Fork of {original_tool.display_name}",
        category=original_tool.category,
        tier=original_tool.tier,
        version="1.0.0",
        created_by=forked_by,
        parent_tool_id=original_tool_id,
        input_schema=original_tool.input_schema,
        output_schema=original_tool.output_schema,
        credit_cost=original_tool.credit_cost,
        is_active=False,  # Needs approval
        is_public=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_tool)
    
    # Create new version
    new_version = ToolVersion(
        id=uuid4(),
        tool_id=new_tool.id,
        version="1.0.0",
        version_number=1,
        code_type=code_type or orig_version.code_type,
        code_content=forked_code,
        system_prompt=orig_version.system_prompt,
        input_schema=orig_version.input_schema,
        output_schema=orig_version.output_schema,
        dependencies=orig_version.dependencies,
        config=orig_version.config,
        status=VersionStatus.PENDING_REVIEW.value,
        is_live=False,
        created_by=forked_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        changelog=changelog,
    )
    db.add(new_version)
    
    # Create fork event
    fork_event = ForkEvent(
        id=uuid4(),
        parent_tool_id=original_tool_id,
        child_tool_id=new_tool.id,
        forked_by=forked_by,
        fork_type="modification",
        attribution_score=attr_score,
        revenue_generated=0,
        revenue_shared=0,
        is_sybil_flagged=is_trivial,
        created_at=datetime.utcnow(),
    )
    db.add(fork_event)
    
    # Create diff record
    tool_diff = ToolDiff(
        id=uuid4(),
        fork_event_id=fork_event.id,
        original_version_id=orig_version.id,
        forked_version_id=new_version.id,
        diff_content=diff_stats["diff_content"],
        lines_added=diff_stats["lines_added"],
        lines_removed=diff_stats["lines_removed"],
        lines_modified=diff_stats["lines_modified"],
        semantic_changes=semantic,
        diff_score=attr_score,
        similarity_ratio=diff_stats["similarity_ratio"],
        is_trivial_change=is_trivial,
        sybil_flags={"score_too_low": is_trivial, "similarity": diff_stats["similarity_ratio"]},
        created_at=datetime.utcnow(),
    )
    db.add(tool_diff)
    
    await db.commit()
    await db.refresh(new_tool)
    await db.refresh(new_version)
    await db.refresh(tool_diff)
    
    logger.info(
        f"Fork created: {new_tool_key}, attr_score={attr_score}, "
        f"trivial={is_trivial}, similarity={diff_stats['similarity_ratio']:.2f}"
    )
    
    return new_tool, new_version, tool_diff


# =============================================================================
# Test Case Management
# =============================================================================

async def copy_test_cases_to_fork(
    db: AsyncSession,
    original_tool_id: UUID,
    forked_tool_id: UUID,
    forked_by: str,
) -> List[ToolTestCase]:
    """Copy test cases from original tool to fork."""
    result = await db.execute(
        select(ToolTestCase)
        .where(ToolTestCase.tool_id == original_tool_id)
        .where(ToolTestCase.is_active == True)
    )
    original_tests = result.scalars().all()
    
    copied = []
    for test in original_tests:
        new_test = ToolTestCase(
            id=uuid4(),
            tool_id=forked_tool_id,
            name=test.name,
            description=test.description,
            input_data=test.input_data,
            expected_output=test.expected_output,
            validation_rules=test.validation_rules,
            is_required=test.is_required,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=forked_by,
        )
        db.add(new_test)
        copied.append(new_test)
    
    await db.commit()
    return copied
