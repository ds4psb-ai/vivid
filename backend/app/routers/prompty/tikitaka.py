"""Prompty Tikitaka Workflow API.

6-step Dual AI (Gemini <-> Claude) workflow for high-quality image/video generation.

SSoT Documentation: viral-video-automation/templates/MODE_TIKITAKA.md
Runtime Prompts: Frontend (frontend/src/lib/tikitaka-prompts.ts)

Backend responsibilities:
- Tikitaka workflow state management (current step, outputs)
- Step advancement and goto logic
- Tool prompts storage (after Claude generates them)

Frontend responsibilities:
- Prompt templates (TIKITAKA_PROMPTS constant)
- UI rendering and copy functionality
"""
from typing import Optional, List, Dict, Literal
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

from app.database import get_db
from app.models_prompty import PromptyProject
from app.dependencies import get_current_user, get_current_user_id

router = APIRouter(prefix="/tikitaka", tags=["prompty-tikitaka"])


# =============================================================================
# SCHEMAS
# =============================================================================

class TikitakaWorkflowState(BaseModel):
    """Tikitaka workflow state (stored in DB)."""
    tikitaka_id: str
    current_step: int = Field(ge=1, le=6, default=1)
    anchor_scene_id: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    step_outputs: Dict[str, str] = Field(default_factory=dict)
    tool_prompts: Dict[str, str] = Field(default_factory=dict)


class TikitakaStartRequest(BaseModel):
    """Request to start tikitaka workflow."""
    anchor_scene_id: Optional[str] = None


class TikitakaStartResponse(BaseModel):
    """Response after starting tikitaka workflow."""
    project_id: UUID
    tikitaka_id: str
    current_step: int
    anchor_scene_id: Optional[str] = None


class TikitakaCurrentResponse(BaseModel):
    """Current tikitaka state."""
    tikitaka_id: str
    current_step: int
    anchor_scene_id: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    tool_prompts: Dict[str, str] = Field(default_factory=dict)


class TikitakaAdvanceRequest(BaseModel):
    """Request to advance to next step."""
    gemini_output: Optional[str] = None
    claude_output: Optional[str] = None
    user_feedback: Optional[str] = None


class TikitakaAdvanceResponse(BaseModel):
    """Response after advancing step."""
    new_step: int
    completed: bool = False


class ToolPrompt(BaseModel):
    """Tool-specific prompt."""
    tool_id: str
    tool_name: str
    prompt_text: str
    external_url: Optional[str] = None
    recommended: bool = False


class ToolPromptsResponse(BaseModel):
    """All tool-specific prompts."""
    prompts: List[ToolPrompt]
    recommended_tool: str


class TikitakaGotoRequest(BaseModel):
    """Request to jump to a specific step."""
    reason: Optional[str] = None  # "REVISE", "REJECT", etc.


# =============================================================================
# TOOL CONFIGS (for URL references)
# =============================================================================

TOOL_CONFIGS = {
    "nanobanana": {
        "name": "NanoBanana",
        "url": "https://nanobanana.ai",
    },
    "midjourney": {
        "name": "MJ V7",
        "url": "https://discord.com/channels/@me",
    },
    "kling": {
        "name": "Kling 2.6",
        "url": "https://klingai.com",
    },
    "veo": {
        "name": "Veo 3.1",
        "url": "https://labs.google/fx/tools/veo",
    },
}


# =============================================================================
# HELPERS
# =============================================================================

def generate_tool_prompts(base_prompt: str) -> Dict[str, str]:
    """Generate tool-specific prompts from base prompt.

    Transforms the base prompt to each tool's preferred format.
    """
    prompts = {}

    # NanoBanana (Korean format)
    prompts["nanobanana"] = f"""[한글 프롬프트]
{base_prompt}

--no 변형된 손, 6개 손가락, 서양인 특징"""

    # MJ V7 (English with params)
    prompts["midjourney"] = f"""{base_prompt}

--ar 16:9 --v 7 --style raw --no deformed hands, 6 fingers, caucasian features"""

    # Kling (English - Image to Video)
    prompts["kling"] = f"""[Image-to-Video Prompt]
{base_prompt}

Duration: 3 seconds
Camera: Subtle dolly in
Motion: Minimal, natural movement"""

    # Veo (English)
    prompts["veo"] = f"""Create a video based on:
{base_prompt}

Style: Photorealistic
Duration: 4 seconds
Motion: Smooth, cinematic"""

    return prompts


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/{project_id}/start", response_model=TikitakaStartResponse)
async def start_tikitaka(
    project_id: UUID,
    data: TikitakaStartRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Start tikitaka workflow for a project.

    Initializes 6-step workflow state in DB.
    """
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Initialize tikitaka state
    tikitaka_id = f"tt_{project_id.hex[:8]}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    tikitaka_state = {
        "tikitaka_id": tikitaka_id,
        "current_step": 1,
        "anchor_scene_id": data.anchor_scene_id,
        "started_at": datetime.utcnow().isoformat(),
        "step_outputs": {},
        "tool_prompts": {},
    }

    state = dict(project.state) if project.state else {}
    state["tikitaka"] = tikitaka_state
    project.state = state
    attributes.flag_modified(project, "state")

    await db.commit()
    await db.refresh(project)

    return TikitakaStartResponse(
        project_id=project_id,
        tikitaka_id=tikitaka_id,
        current_step=1,
        anchor_scene_id=data.anchor_scene_id,
    )


@router.get("/{project_id}/current", response_model=TikitakaCurrentResponse)
async def get_current_state(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current tikitaka workflow state."""
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    state = project.state or {}
    tikitaka = state.get("tikitaka")

    if not tikitaka:
        raise HTTPException(status_code=400, detail="Tikitaka workflow not started")

    return TikitakaCurrentResponse(
        tikitaka_id=tikitaka.get("tikitaka_id", ""),
        current_step=tikitaka.get("current_step", 1),
        anchor_scene_id=tikitaka.get("anchor_scene_id"),
        started_at=tikitaka.get("started_at", ""),
        completed_at=tikitaka.get("completed_at"),
        tool_prompts=tikitaka.get("tool_prompts", {}),
    )


@router.post("/{project_id}/advance", response_model=TikitakaAdvanceResponse)
async def advance_step(
    project_id: UUID,
    data: TikitakaAdvanceRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Advance to the next tikitaka step.

    Stores output from current step and moves to next.
    """
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    state = project.state or {}
    tikitaka = state.get("tikitaka")

    if not tikitaka:
        raise HTTPException(status_code=400, detail="Tikitaka workflow not started")

    current_step = tikitaka.get("current_step", 1)

    # Store output for current step
    step_outputs = tikitaka.get("step_outputs", {})
    if data.gemini_output:
        step_outputs[f"step_{current_step}_gemini"] = data.gemini_output
    if data.claude_output:
        step_outputs[f"step_{current_step}_claude"] = data.claude_output
        # Generate tool prompts from Claude output (step 2 or 4)
        if current_step in (2, 4):
            tikitaka["tool_prompts"] = generate_tool_prompts(data.claude_output)
    if data.user_feedback:
        step_outputs[f"step_{current_step}_feedback"] = data.user_feedback

    tikitaka["step_outputs"] = step_outputs

    # Advance to next step
    if current_step >= 6:
        # Workflow completed
        tikitaka["completed_at"] = datetime.utcnow().isoformat()
        state["tikitaka"] = tikitaka
        project.state = state
        attributes.flag_modified(project, "state")
        await db.commit()

        return TikitakaAdvanceResponse(new_step=6, completed=True)

    new_step = current_step + 1
    tikitaka["current_step"] = new_step
    state["tikitaka"] = tikitaka
    project.state = state
    attributes.flag_modified(project, "state")

    await db.commit()

    return TikitakaAdvanceResponse(new_step=new_step, completed=False)


@router.get("/{project_id}/prompts", response_model=ToolPromptsResponse)
async def get_tool_prompts(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get tool-specific prompts for the project.

    Available after Step 2 (Draft) or Step 4 (Revise).
    """
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    state = project.state or {}
    tikitaka = state.get("tikitaka", {})
    stored_prompts = tikitaka.get("tool_prompts", {})

    if not stored_prompts:
        raise HTTPException(
            status_code=400,
            detail="No tool prompts available. Complete Step 2 (Draft) first.",
        )

    prompts = []
    for tool_id, config in TOOL_CONFIGS.items():
        prompt_text = stored_prompts.get(tool_id, "")
        prompts.append(ToolPrompt(
            tool_id=tool_id,
            tool_name=config["name"],
            prompt_text=prompt_text,
            external_url=config["url"],
            recommended=(tool_id == "nanobanana"),
        ))

    return ToolPromptsResponse(
        prompts=prompts,
        recommended_tool="nanobanana",
    )


@router.post("/{project_id}/goto/{step}")
async def goto_step(
    project_id: UUID,
    step: int,
    data: TikitakaGotoRequest = TikitakaGotoRequest(),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Jump to a specific tikitaka step.

    Useful for:
    - REVISE: Going back to step 2 after REJECT verdict
    - Retrying: Going back to step 5 after micro-adjust
    """
    if step < 1 or step > 6:
        raise HTTPException(status_code=400, detail="Step must be between 1 and 6")

    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    state = project.state or {}
    tikitaka = state.get("tikitaka")

    if not tikitaka:
        raise HTTPException(status_code=400, detail="Tikitaka workflow not started")

    # Log the goto action if reason provided
    if data.reason:
        step_outputs = tikitaka.get("step_outputs", {})
        step_outputs[f"goto_{step}_reason"] = data.reason
        tikitaka["step_outputs"] = step_outputs

    tikitaka["current_step"] = step
    tikitaka["completed_at"] = None  # Reset completion if going back
    state["tikitaka"] = tikitaka
    project.state = state
    attributes.flag_modified(project, "state")

    await db.commit()

    return {"step": step, "reason": data.reason}


@router.patch("/{project_id}/anchor")
async def set_anchor_scene(
    project_id: UUID,
    anchor_scene_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Set or update the anchor scene for tikitaka workflow."""
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    state = project.state or {}
    tikitaka = state.get("tikitaka")

    if not tikitaka:
        raise HTTPException(status_code=400, detail="Tikitaka workflow not started")

    tikitaka["anchor_scene_id"] = anchor_scene_id
    state["tikitaka"] = tikitaka
    project.state = state
    attributes.flag_modified(project, "state")

    await db.commit()

    return {"anchor_scene_id": anchor_scene_id}
