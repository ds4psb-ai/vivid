"""Prompty Critique API.

Quality assessment for workflow steps.
Based on CRITIQUE_*.md checklists from viral-video-automation.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

from app.database import get_db
from app.models_prompty import PromptyCritique, PromptyProject, PromptyTemplate
from app.dependencies import get_current_user, get_current_user_id

router = APIRouter(prefix="/critique", tags=["prompty-critique"])


# =============================================================================
# SCHEMAS
# =============================================================================

class CritiqueScore(BaseModel):
    """Individual checklist item score."""
    score: int = Field(..., ge=1, le=10)
    notes: Optional[str] = None


class CritiqueSubmit(BaseModel):
    """Submit critique scores for a step."""
    project_id: UUID
    stage: str
    step_id: str
    scores: dict[str, CritiqueScore]  # {"composition": {"score": 8, "notes": "..."}}
    notes: Optional[str] = None


class CritiqueResponse(BaseModel):
    """Critique result."""
    id: UUID
    project_id: UUID
    stage: str
    step_id: str
    scores: dict
    total_score: float
    passed: bool
    revision_number: int
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CritiqueHistoryResponse(BaseModel):
    """Critique history for a project."""
    items: List[CritiqueResponse]
    average_score: float
    total_critiques: int
    pass_rate: float


# =============================================================================
# SCORE CALCULATION
# =============================================================================

def calculate_total_score(scores: dict, critique_config: dict) -> tuple[float, bool]:
    """Calculate weighted total score and pass/fail status.

    Args:
        scores: {"composition": {"score": 8}, "consistency": {"score": 9}}
        critique_config: {"items": [{"id": "composition", "weight": 0.15}], "passing_score": 75}

    Returns:
        (total_score: 0-100, passed: bool)
    """
    items = critique_config.get("items", [])
    passing_score = critique_config.get("passing_score", 75)

    if not items:
        # No config - simple average
        if not scores:
            return 0.0, False
        total = sum(s.get("score", 0) for s in scores.values())
        avg = (total / len(scores)) * 10  # Scale 1-10 to 0-100
        return avg, avg >= passing_score

    # Weighted calculation
    total_weight = 0.0
    weighted_sum = 0.0

    for item in items:
        item_id = item.get("id")
        weight = item.get("weight", 0.1)

        if item_id in scores:
            score = scores[item_id].get("score", 0)
            weighted_sum += score * weight * 10  # Scale 1-10 to 0-100
            total_weight += weight

    if total_weight == 0:
        return 0.0, False

    total_score = weighted_sum / total_weight
    return round(total_score, 1), total_score >= passing_score


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("", response_model=CritiqueResponse, status_code=201)
async def submit_critique(
    data: CritiqueSubmit,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Submit critique scores for a workflow step.

    Calculates total score based on template's critique config.
    """
    # Verify project ownership
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == data.project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get critique config from template
    critique_config = {}
    if project.template_id:
        template_result = await db.execute(
            select(PromptyTemplate).where(PromptyTemplate.id == project.template_id)
        )
        template = template_result.scalar_one_or_none()
        if template:
            critique_config = template.critique_config or {}

    # Convert scores to dict format
    scores_dict = {k: v.model_dump() for k, v in data.scores.items()}

    # Calculate total score
    total_score, passed = calculate_total_score(scores_dict, critique_config)

    # Count existing critiques for this step (for revision number)
    count_result = await db.execute(
        select(func.count()).where(
            PromptyCritique.project_id == data.project_id,
            PromptyCritique.stage == data.stage,
            PromptyCritique.step_id == data.step_id,
        )
    )
    revision_number = (count_result.scalar() or 0) + 1

    # Create critique
    critique = PromptyCritique(
        project_id=data.project_id,
        stage=data.stage,
        step_id=data.step_id,
        scores=scores_dict,
        total_score=total_score,
        passed=passed,
        revision_number=revision_number,
        notes=data.notes,
    )

    db.add(critique)

    # Update project state if passed
    if passed:
        state = project.state or {}
        stages = state.get("stages", {})
        stage_state = stages.get(data.stage, {})

        # Mark step as completed
        if data.step_id:
            stage_state[data.step_id] = {
                "status": "completed",
                "score": total_score,
                "revision": revision_number,
            }
        else:
            stage_state["status"] = "completed"

        stages[data.stage] = stage_state
        state["stages"] = stages
        state["last_activity"] = datetime.utcnow().isoformat()
        project.state = state
        attributes.flag_modified(project, "state")

        # Calculate overall progress
        total_stages = len(stages)
        completed = sum(
            1 for s in stages.values()
            if s.get("status") == "completed" or
            all(step.get("status") == "completed" for step in s.values() if isinstance(step, dict))
        )
        project.progress_percent = int((completed / total_stages) * 100) if total_stages > 0 else 0

    await db.commit()
    await db.refresh(critique)

    return CritiqueResponse(
        id=critique.id,
        project_id=critique.project_id,
        stage=critique.stage,
        step_id=critique.step_id,
        scores=critique.scores,
        total_score=critique.total_score,
        passed=critique.passed,
        revision_number=critique.revision_number,
        notes=critique.notes,
        created_at=critique.created_at,
    )


@router.get("/{project_id}", response_model=CritiqueHistoryResponse)
async def get_critique_history(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get critique history for a project."""
    # Verify project ownership
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all critiques
    result = await db.execute(
        select(PromptyCritique)
        .where(PromptyCritique.project_id == project_id)
        .order_by(desc(PromptyCritique.created_at))
    )
    critiques = result.scalars().all()

    # Calculate stats
    total = len(critiques)
    if total == 0:
        return CritiqueHistoryResponse(
            items=[],
            average_score=0.0,
            total_critiques=0,
            pass_rate=0.0,
        )

    avg_score = sum(c.total_score for c in critiques) / total
    passed_count = sum(1 for c in critiques if c.passed)
    pass_rate = (passed_count / total) * 100

    return CritiqueHistoryResponse(
        items=[
            CritiqueResponse(
                id=c.id,
                project_id=c.project_id,
                stage=c.stage,
                step_id=c.step_id,
                scores=c.scores,
                total_score=c.total_score,
                passed=c.passed,
                revision_number=c.revision_number,
                notes=c.notes,
                created_at=c.created_at,
            )
            for c in critiques
        ],
        average_score=round(avg_score, 1),
        total_critiques=total,
        pass_rate=round(pass_rate, 1),
    )


@router.get("/{project_id}/{step_id}", response_model=Optional[CritiqueResponse])
async def get_step_critique(
    project_id: UUID,
    step_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get the latest critique for a specific step.

    Returns the most recent critique for the given project and step,
    or null if no critique exists.
    """
    # Verify project ownership
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest critique for this step
    result = await db.execute(
        select(PromptyCritique)
        .where(
            PromptyCritique.project_id == project_id,
            PromptyCritique.step_id == step_id,
        )
        .order_by(desc(PromptyCritique.created_at))
        .limit(1)
    )
    critique = result.scalar_one_or_none()

    if not critique:
        return None

    return CritiqueResponse(
        id=critique.id,
        project_id=critique.project_id,
        stage=critique.stage,
        step_id=critique.step_id,
        scores=critique.scores,
        total_score=critique.total_score,
        passed=critique.passed,
        revision_number=critique.revision_number,
        notes=critique.notes,
        created_at=critique.created_at,
    )
