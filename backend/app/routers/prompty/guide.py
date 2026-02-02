"""Prompty Workflow Guide API.

Step-by-step guide navigation and prompt delivery.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

from app.database import get_db
from app.models_prompty import PromptyProject, PromptyTemplate, PromptyGuideLog
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/guide", tags=["prompty-guide"])


# =============================================================================
# SCHEMAS
# =============================================================================

class StepInfo(BaseModel):
    """Information about a workflow step."""
    id: str
    name: str
    description: Optional[str] = None
    prompt_text: Optional[str] = None
    prompt_file: Optional[str] = None
    external_tool: Optional[str] = None  # nanobanana, kling, etc.
    external_url: Optional[str] = None
    tips: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed
    score: Optional[float] = None


class StageInfo(BaseModel):
    """Information about a workflow stage."""
    id: str
    name: str
    description: Optional[str] = None
    steps: List[StepInfo] = Field(default_factory=list)
    status: str = "pending"


class GuideResponse(BaseModel):
    """Current guide state for a project."""
    project_id: UUID
    project_name: str
    current_stage: str
    current_step: str
    progress_percent: int
    stages: List[StageInfo]
    current_step_info: Optional[StepInfo] = None


class NextStepResponse(BaseModel):
    """Response after advancing to next step."""
    new_stage: str
    new_step: str
    completed: bool = False


class LogActionRequest(BaseModel):
    """Log a guide action."""
    action: str  # copy_prompt, open_external, complete_step
    stage: Optional[str] = None
    step_id: Optional[str] = None
    extra_data: dict = Field(default_factory=dict)


# =============================================================================
# DEFAULT WORKFLOW
# =============================================================================

DEFAULT_WORKFLOW = {
    "stages": ["analysis", "image", "video", "assembly"],
    "steps": {
        "analysis": [
            {
                "id": "analyze_reference",
                "name": "레퍼런스 분석",
                "description": "원본 영상의 스타일, 구성, 연출을 분석합니다.",
                "prompt_text": "Analyze this video reference and extract: visual style, color palette, camera movements, scene transitions, mood/tone, and key visual elements.",
                "tips": [
                    "영상의 전체 톤을 먼저 파악하세요",
                    "컷 전환 타이밍을 노트하세요",
                    "색 보정 스타일을 기록하세요",
                ],
            },
        ],
        "image": [
            {
                "id": "anchor_girl",
                "name": "앵커 걸",
                "description": "주인공 여성 캐릭터의 기준 이미지를 생성합니다.",
                "prompt_text": "Create a consistent anchor character: young woman, photorealistic, neutral expression, studio lighting. --no deformed hands, 6 fingers",
                "external_tool": "nanobanana",
                "tips": [
                    "--no 파라미터로 흔한 오류를 방지하세요",
                    "손 디테일에 특히 주의하세요",
                    "조명은 일관되게 유지하세요",
                ],
            },
            {
                "id": "anchor_boy",
                "name": "앵커 보이",
                "description": "주인공 남성 캐릭터의 기준 이미지를 생성합니다.",
                "prompt_text": "Create a consistent anchor character: young man, photorealistic, neutral expression, studio lighting. --no deformed hands, 6 fingers",
                "external_tool": "nanobanana",
                "tips": ["동일한 조명 설정을 사용하세요", "앵커 걸과 스타일을 맞추세요"],
            },
        ],
        "video": [
            {
                "id": "scene_assembly",
                "name": "장면 조립",
                "description": "이미지들을 영상으로 변환합니다.",
                "prompt_text": "Transform static images into video clips with subtle motion. Duration: 2-4 seconds per scene.",
                "external_tool": "kling",
                "tips": ["자연스러운 움직임을 추가하세요", "과한 모션은 피하세요"],
            },
        ],
        "assembly": [
            {
                "id": "final_edit",
                "name": "최종 편집",
                "description": "모든 클립을 편집하고 사운드를 추가합니다.",
                "prompt_text": "Assemble all video clips, add transitions, color grade, and add music/sound effects.",
                "external_tool": "davinci",
                "tips": ["음악과 비트를 맞추세요", "컬러 그레이딩으로 통일감을 주세요"],
            },
        ],
    },
}


# =============================================================================
# HELPERS
# =============================================================================

def get_workflow_config(template: Optional[PromptyTemplate]) -> dict:
    """Get workflow config from template or use default."""
    if template and template.workflow_config:
        return template.workflow_config
    return DEFAULT_WORKFLOW


def build_stages_info(workflow_config: dict, project_state: dict) -> List[StageInfo]:
    """Build stage info list with current status."""
    stages = workflow_config.get("stages", [])
    steps_config = workflow_config.get("steps", {})
    state_stages = project_state.get("stages", {})

    result = []
    for stage_id in stages:
        stage_steps = steps_config.get(stage_id, [])
        stage_state = state_stages.get(stage_id, {})

        steps_info = []
        for step in stage_steps:
            step_id = step.get("id", "")
            step_state = stage_state.get(step_id, {})

            status = step_state.get("status", "pending")
            score = step_state.get("score")

            steps_info.append(StepInfo(
                id=step_id,
                name=step.get("name", ""),
                description=step.get("description"),
                prompt_text=step.get("prompt_text"),
                prompt_file=step.get("prompt_file"),
                external_tool=step.get("external_tool"),
                external_url=step.get("external_url"),
                tips=step.get("tips", []),
                status=status,
                score=score,
            ))

        # Determine stage status
        if all(s.status == "completed" for s in steps_info):
            stage_status = "completed"
        elif any(s.status in ("in_progress", "completed") for s in steps_info):
            stage_status = "in_progress"
        else:
            stage_status = "pending"

        result.append(StageInfo(
            id=stage_id,
            name=stage_id.title(),
            steps=steps_info,
            status=stage_status,
        ))

    return result


def find_current_step_info(stages_info: List[StageInfo], current_stage: str, current_step: str) -> Optional[StepInfo]:
    """Find the current step info."""
    for stage in stages_info:
        if stage.id == current_stage:
            for step in stage.steps:
                if step.id == current_step:
                    return step
            # If current_step not specified, return first pending step
            if not current_step:
                for step in stage.steps:
                    if step.status == "pending":
                        return step
            break
    return None


def find_next_step(stages_info: List[StageInfo], current_stage: str, current_step: str) -> tuple[str, str, bool]:
    """Find the next step after current.

    Returns:
        (next_stage, next_step, is_completed)
    """
    # current_step이 비어있으면 첫 번째 pending step 찾기
    if not current_step:
        for stage in stages_info:
            for step in stage.steps:
                if step.status != "completed":
                    return stage.id, step.id, False
        return current_stage, "", True  # 모든 step 완료

    # 기존 로직: current_step 이후의 다음 pending step 찾기
    found_current = False

    for stage in stages_info:
        for step in stage.steps:
            if found_current and step.status != "completed":
                return stage.id, step.id, False

            if stage.id == current_stage and step.id == current_step:
                found_current = True

    # No more steps - completed
    return current_stage, current_step, True


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/{project_id}", response_model=GuideResponse)
async def get_guide(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current workflow guide state for a project."""
    # Get project
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get template if exists
    template = None
    if project.template_id:
        template_result = await db.execute(
            select(PromptyTemplate).where(PromptyTemplate.id == project.template_id)
        )
        template = template_result.scalar_one_or_none()

    # Build guide
    workflow_config = get_workflow_config(template)
    stages_info = build_stages_info(workflow_config, project.state or {})
    current_step_info = find_current_step_info(stages_info, project.current_stage, project.current_step)

    return GuideResponse(
        project_id=project.id,
        project_name=project.name,
        current_stage=project.current_stage,
        current_step=project.current_step,
        progress_percent=project.progress_percent,
        stages=stages_info,
        current_step_info=current_step_info,
    )


@router.post("/{project_id}/next", response_model=NextStepResponse)
async def advance_to_next_step(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Advance to the next workflow step.

    Marks current step as in_progress and finds next pending step.
    """
    # Get project
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get template
    template = None
    if project.template_id:
        template_result = await db.execute(
            select(PromptyTemplate).where(PromptyTemplate.id == project.template_id)
        )
        template = template_result.scalar_one_or_none()

    # Build guide
    workflow_config = get_workflow_config(template)
    stages_info = build_stages_info(workflow_config, project.state or {})

    # Find next step
    next_stage, next_step, completed = find_next_step(
        stages_info, project.current_stage, project.current_step
    )

    # Update project
    project.current_stage = next_stage
    project.current_step = next_step

    if completed:
        project.status = "completed"
        project.completed_at = datetime.utcnow()
        project.progress_percent = 100

    # Update state
    state = project.state or {}
    state["last_activity"] = datetime.utcnow().isoformat()
    project.state = state
    attributes.flag_modified(project, "state")

    await db.commit()

    return NextStepResponse(
        new_stage=next_stage,
        new_step=next_step,
        completed=completed,
    )


@router.post("/{project_id}/log", status_code=204)
async def log_action(
    project_id: UUID,
    data: LogActionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Log a guide action for analytics.

    Actions: copy_prompt, open_external, complete_step, submit_critique
    """
    # Verify project exists
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create log entry
    log = PromptyGuideLog(
        project_id=project_id,
        user_id=user_id,
        action=data.action,
        stage=data.stage,
        step_id=data.step_id,
        extra_data=data.extra_data,
    )

    db.add(log)
    await db.commit()
