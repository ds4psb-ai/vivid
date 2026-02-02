"""Prompty STATE.md Sync API.

Handles bidirectional sync between local STATE.md files and database.
This is the core of the "Local Project Folder (SSoT)" architecture.
"""
import re
from typing import Optional, List
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


router = APIRouter(prefix="/state", tags=["prompty-state"])


# =============================================================================
# SCHEMAS
# =============================================================================

class SceneProgress(BaseModel):
    """Individual scene progress from STATE.md."""
    scene: str
    description: str
    image_status: str  # "v2/scene01.png" or "작업 중" or "-"
    video_status: str  # "selected/scene01.mp4" or "-"
    status_emoji: str  # "✅ 확정" or "🔄 진행" or "⏳ 대기"


class StageProgress(BaseModel):
    """Stage progress with percentage."""
    stage_id: str  # stage1, stage2, stage3, stage4
    name: str  # ANALYZE, IMAGE, VIDEO, ASSEMBLY
    percent: int  # 0-100
    bar: str  # "████████░░"


class StateMdParsed(BaseModel):
    """Parsed STATE.md content."""
    scenes: List[SceneProgress]
    stages: List[StageProgress]
    current_task: Optional[str] = None
    anchor_scene: Optional[str] = None  # Scene marked as ANCHOR
    tikitaka_count: int = 0


class StateSyncRequest(BaseModel):
    """Request to sync STATE.md content."""
    state_md_content: str = Field(..., description="Raw STATE.md file content")


class StateSyncResponse(BaseModel):
    """Response from sync operation."""
    synced: bool
    progress_percent: int
    current_stage: str
    current_step: str
    scenes_total: int
    scenes_completed: int
    anchor_scene: Optional[str]


class StateExportResponse(BaseModel):
    """Exported STATE.md content."""
    content: str
    last_synced: Optional[datetime]


# =============================================================================
# STATE.MD PARSER
# =============================================================================

def parse_scene_progress_table(content: str) -> List[SceneProgress]:
    """Parse Scene Progress markdown table.

    Expected format:
    | Scene | Description | Image | Video | Status |
    |-------|-------------|-------|-------|--------|
    | 1 | Arrival | v2/scene01.png | - | ✅ 확정 |
    | 2 | Anticipation (ANCHOR) | v3/scene02.png | - | ✅ 확정 |
    """
    scenes = []

    # Find Scene Progress section
    section_match = re.search(
        r'##\s*Scene\s+Progress\s*\n([\s\S]*?)(?=\n##|\Z)',
        content,
        re.IGNORECASE
    )

    if not section_match:
        return scenes

    section_content = section_match.group(1)

    # Parse table rows (skip header and separator)
    table_pattern = re.compile(
        r'\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
    )

    for match in table_pattern.finditer(section_content):
        scene_num = match.group(1).strip()
        description = match.group(2).strip()
        image = match.group(3).strip()
        video = match.group(4).strip()
        status = match.group(5).strip()

        scenes.append(SceneProgress(
            scene=scene_num,
            description=description,
            image_status=image,
            video_status=video,
            status_emoji=status,
        ))

    return scenes


def parse_overall_progress(content: str) -> List[StageProgress]:
    """Parse Overall Progress section.

    Expected format:
    ## Overall Progress
    - Stage 1: ANALYZE ████████░░ 80%
    - Stage 2: IMAGE   ██████░░░░ 60%
    """
    stages = []

    # Find Overall Progress section
    section_match = re.search(
        r'##\s*Overall\s+Progress\s*\n([\s\S]*?)(?=\n##|\Z)',
        content,
        re.IGNORECASE
    )

    if not section_match:
        return stages

    section_content = section_match.group(1)

    # Parse progress lines
    progress_pattern = re.compile(
        r'-\s*Stage\s+(\d+):\s*(\w+)\s+([\u2588\u2591░█]+)\s*(\d+)%',
        re.UNICODE
    )

    for match in progress_pattern.finditer(section_content):
        stage_num = match.group(1)
        name = match.group(2).strip()
        bar = match.group(3).strip()
        percent = int(match.group(4))

        stages.append(StageProgress(
            stage_id=f"stage{stage_num}",
            name=name,
            percent=percent,
            bar=bar,
        ))

    return stages


def parse_current_task(content: str) -> Optional[str]:
    """Parse Current Task section.

    Expected format:
    ## Current Task
    Scene 04 이미지 생성 (ANCHOR 레퍼런스 적용)
    """
    match = re.search(
        r'##\s*Current\s+Task\s*\n\s*(.+)',
        content,
        re.IGNORECASE
    )
    return match.group(1).strip() if match else None


def find_anchor_scene(scenes: List[SceneProgress]) -> Optional[str]:
    """Find the ANCHOR scene from parsed scenes."""
    for scene in scenes:
        if "(ANCHOR)" in scene.description.upper():
            return scene.scene
    return None


def count_tikitaka_iterations(content: str) -> int:
    """Count tikitaka iterations from critique log section."""
    matches = re.findall(r'#\d+', content)
    if not matches:
        return 0
    # Find highest iteration number
    numbers = [int(m[1:]) for m in matches]
    return max(numbers) if numbers else 0


def parse_state_md(content: str) -> StateMdParsed:
    """Parse complete STATE.md content into structured data."""
    scenes = parse_scene_progress_table(content)
    stages = parse_overall_progress(content)
    current_task = parse_current_task(content)
    anchor_scene = find_anchor_scene(scenes)
    tikitaka_count = count_tikitaka_iterations(content)

    return StateMdParsed(
        scenes=scenes,
        stages=stages,
        current_task=current_task,
        anchor_scene=anchor_scene,
        tikitaka_count=tikitaka_count,
    )


# =============================================================================
# STATE.MD GENERATOR
# =============================================================================

def generate_progress_bar(percent: int, width: int = 10) -> str:
    """Generate ASCII progress bar."""
    filled = int(width * percent / 100)
    empty = width - filled
    return "█" * filled + "░" * empty


def generate_state_md(project: PromptyProject) -> str:
    """Generate STATE.md content from project state."""
    state = project.state or {}
    stages = state.get("stages", {})
    current_step = state.get("current_step", "")

    lines = [
        "# STATE.md",
        f"# Project: {project.name}",
        f"# Last Updated: {datetime.utcnow().isoformat()}Z",
        "",
        "## Scene Progress",
        "| Scene | Description | Image | Video | Status |",
        "|-------|-------------|-------|-------|--------|",
    ]

    # Generate scene rows from state
    image_stage = stages.get("stage2", stages.get("image", {}))
    video_stage = stages.get("stage3", stages.get("video", {}))

    scene_num = 1
    for step_id, step_data in image_stage.items():
        if isinstance(step_data, dict):
            status = step_data.get("status", "pending")
            image_path = step_data.get("image_path", "-")
            video_path = video_stage.get(step_id, {}).get("video_path", "-") if isinstance(video_stage.get(step_id), dict) else "-"

            status_emoji = "✅ 확정" if status == "completed" else "🔄 진행" if status == "in_progress" else "⏳ 대기"
            description = step_data.get("description", step_id)

            lines.append(f"| {scene_num} | {description} | {image_path} | {video_path} | {status_emoji} |")
            scene_num += 1

    lines.extend([
        "",
        "## Overall Progress",
    ])

    stage_names = ["ANALYZE", "IMAGE", "VIDEO", "ASSEMBLY"]
    stage_keys = ["stage1", "stage2", "stage3", "stage4"]

    for i, (key, name) in enumerate(zip(stage_keys, stage_names)):
        stage_data = stages.get(key, {})
        if isinstance(stage_data, dict):
            # Calculate stage progress
            if stage_data.get("status") == "completed":
                percent = 100
            elif not stage_data:
                percent = 0
            else:
                completed = sum(1 for v in stage_data.values() if isinstance(v, dict) and v.get("status") == "completed")
                total = sum(1 for v in stage_data.values() if isinstance(v, dict))
                percent = int((completed / total) * 100) if total > 0 else 0
        else:
            percent = 0

        bar = generate_progress_bar(percent)
        lines.append(f"- Stage {i + 1}: {name} {bar} {percent}%")

    if current_step:
        lines.extend([
            "",
            "## Current Task",
            current_step,
        ])

    return "\n".join(lines)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/{project_id}/sync", response_model=StateSyncResponse)
async def sync_state_from_local(
    project_id: UUID,
    data: StateSyncRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Sync local STATE.md to database.

    Parses the STATE.md content and updates the project state in DB.
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

    # Parse STATE.md
    parsed = parse_state_md(data.state_md_content)

    # Build state dict
    state = project.state or {}
    stages = state.get("stages", {})

    # Update scene progress
    image_stage = {}
    for scene in parsed.scenes:
        is_anchor = "(ANCHOR)" in scene.description.upper()
        status = "completed" if "✅" in scene.status_emoji else "in_progress" if "🔄" in scene.status_emoji else "pending"

        image_stage[f"scene{scene.scene}"] = {
            "status": status,
            "description": scene.description,
            "image_path": scene.image_status if scene.image_status != "-" else None,
            "is_anchor": is_anchor,
        }

    if image_stage:
        stages["stage2"] = image_stage

    # Update stage progress
    for stage in parsed.stages:
        stage_key = stage.stage_id
        if stage_key not in stages:
            stages[stage_key] = {}
        if isinstance(stages[stage_key], dict):
            stages[stage_key]["_progress"] = stage.percent
            if stage.percent == 100:
                stages[stage_key]["status"] = "completed"

    state["stages"] = stages
    state["current_step"] = parsed.current_task
    state["last_activity"] = datetime.utcnow().isoformat()
    state["tikitaka_count"] = parsed.tikitaka_count

    project.state = state
    attributes.flag_modified(project, "state")

    # Calculate overall progress
    total_stages = len(parsed.stages) or 4
    total_percent = sum(s.percent for s in parsed.stages)
    project.progress_percent = int(total_percent / total_stages) if total_stages > 0 else 0

    # Update current stage based on progress
    for stage in parsed.stages:
        if stage.percent < 100:
            project.current_stage = stage.stage_id
            break
    else:
        project.current_stage = "stage4"

    # Count completed scenes
    scenes_completed = sum(1 for s in parsed.scenes if "✅" in s.status_emoji)

    await db.commit()

    return StateSyncResponse(
        synced=True,
        progress_percent=project.progress_percent,
        current_stage=project.current_stage,
        current_step=parsed.current_task or "",
        scenes_total=len(parsed.scenes),
        scenes_completed=scenes_completed,
        anchor_scene=parsed.anchor_scene,
    )


@router.get("/{project_id}/state.md", response_model=StateExportResponse)
async def export_state_md(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Export project state as STATE.md format.

    Generates STATE.md content from the current database state.
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

    content = generate_state_md(project)
    last_synced = None

    state = project.state or {}
    if state.get("last_activity"):
        try:
            last_synced = datetime.fromisoformat(state["last_activity"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    return StateExportResponse(
        content=content,
        last_synced=last_synced,
    )


@router.get("/{project_id}/parsed", response_model=StateMdParsed)
async def get_parsed_state(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get parsed state from database.

    Returns the structured state data without regenerating STATE.md.
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

    # Convert DB state to parsed format
    state = project.state or {}
    stages_data = state.get("stages", {})

    scenes = []
    image_stage = stages_data.get("stage2", {})
    video_stage = stages_data.get("stage3", {})

    for step_id, step_data in image_stage.items():
        if isinstance(step_data, dict) and step_id.startswith("scene"):
            scene_num = step_id.replace("scene", "")
            status = step_data.get("status", "pending")
            status_emoji = "✅ 확정" if status == "completed" else "🔄 진행" if status == "in_progress" else "⏳ 대기"

            video_data = video_stage.get(step_id, {})

            scenes.append(SceneProgress(
                scene=scene_num,
                description=step_data.get("description", ""),
                image_status=step_data.get("image_path") or "-",
                video_status=video_data.get("video_path") if isinstance(video_data, dict) else "-",
                status_emoji=status_emoji,
            ))

    stages = []
    stage_names = ["ANALYZE", "IMAGE", "VIDEO", "ASSEMBLY"]
    for i, name in enumerate(stage_names):
        stage_key = f"stage{i + 1}"
        stage_data = stages_data.get(stage_key, {})
        percent = stage_data.get("_progress", 0) if isinstance(stage_data, dict) else 0

        stages.append(StageProgress(
            stage_id=stage_key,
            name=name,
            percent=percent,
            bar=generate_progress_bar(percent),
        ))

    anchor_scene = None
    for scene in scenes:
        if "(ANCHOR)" in scene.description.upper():
            anchor_scene = scene.scene
            break

    return StateMdParsed(
        scenes=scenes,
        stages=stages,
        current_task=state.get("current_step"),
        anchor_scene=anchor_scene,
        tikitaka_count=state.get("tikitaka_count", 0),
    )
