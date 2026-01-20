"""IP Generate Demo API router.

투자자 데모용 간소화된 워크플로우 추천 엔드포인트.
실제 생성 없이 프롬프트 분석 → 워크플로우 추천 → 리다이렉트 URL 반환.

데모 종료 후 이 파일은 삭제 가능합니다.
"""

import logging
import re
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ip", tags=["ip-demo"])


# =============================================================================
# Workflow Templates (Hardcoded for Demo)
# =============================================================================

WORKFLOW_TEMPLATES = {
    "character-variation": {
        "name_ko": "캐릭터 변주",
        "name_en": "Character Variation",
        "steps": [
            {"app": "reference-decoder", "href": "/dimension/reference-decoder", "badge": "4D", "name_ko": "레퍼런스 분석", "name_en": "Reference Decode"},
            {"app": "abyss-mirror", "href": "/dimension/abyss", "badge": "AI", "name_ko": "페르소나 변주", "name_en": "Persona Remix"},
            {"app": "story-architect", "href": "/dimension/story-architect", "badge": "2D", "name_ko": "스토리 생성", "name_en": "Story Generate"},
            {"app": "video-maker", "href": "/dimension/video-maker", "badge": "VEO", "name_ko": "영상 생성", "name_en": "Video Generate"},
        ],
    },
    "style-remix": {
        "name_ko": "스타일 리믹스",
        "name_en": "Style Remix",
        "steps": [
            {"app": "reference-decoder", "href": "/dimension/reference-decoder", "badge": "4D", "name_ko": "레퍼런스 분석", "name_en": "Reference Decode"},
            {"app": "aesthetic-director", "href": "/dimension/aesthetic", "badge": "AD", "name_ko": "스타일 가이드", "name_en": "Style Guide"},
            {"app": "visual-realizer", "href": "/dimension/visual-realizer", "badge": "3D", "name_ko": "비주얼 생성", "name_en": "Visual Generate"},
            {"app": "video-maker", "href": "/dimension/video-maker", "badge": "VEO", "name_ko": "영상 생성", "name_en": "Video Generate"},
        ],
    },
    "scene-extension": {
        "name_ko": "씬 확장",
        "name_en": "Scene Extension",
        "steps": [
            {"app": "reference-decoder", "href": "/dimension/reference-decoder", "badge": "4D", "name_ko": "씬 분석", "name_en": "Scene Analysis"},
            {"app": "story-architect", "href": "/dimension/story-architect", "badge": "2D", "name_ko": "스토리 확장", "name_en": "Story Extension"},
            {"app": "visual-realizer", "href": "/dimension/visual-realizer", "badge": "3D", "name_ko": "키프레임 생성", "name_en": "Keyframe Generate"},
            {"app": "video-maker", "href": "/dimension/video-maker", "badge": "VEO", "name_ko": "영상 생성", "name_en": "Video Generate"},
        ],
    },
    "anime-mv": {
        "name_ko": "애니메이션 MV",
        "name_en": "Animation MV",
        "steps": [
            {"app": "reference-decoder", "href": "/dimension/reference-decoder", "badge": "필수", "name_ko": "씬별 분석", "name_en": "Scene Analysis"},
            {"app": "abyss-mirror", "href": "/dimension/abyss", "badge": "필수", "name_ko": "캐릭터 DNA", "name_en": "Character DNA"},
            {"app": "aesthetic-director", "href": "/dimension/aesthetic", "badge": "스타일", "name_ko": "스타일 가이드", "name_en": "Style Guide"},
            {"app": "visual-realizer", "href": "/dimension/visual-realizer", "badge": "일관성", "name_ko": "캐릭터 일관성", "name_en": "Character Consistency"},
            {"app": "sound-crafter", "href": "/dimension/suno", "badge": "BGM", "name_ko": "BGM 생성", "name_en": "BGM Generation"},
            {"app": "video-maker", "href": "/dimension/video-maker", "badge": "씬생성", "name_ko": "씬별 영상 생성", "name_en": "Scene Generation"},
        ],
    },
}

# Keyword patterns for workflow recommendation
KEYWORD_PATTERNS = {
    "character-variation": ["캐릭터", "character", "인물", "성격", "페르소나", "persona", "변주", "variation"],
    "style-remix": ["스타일", "style", "미학", "aesthetic", "색감", "color", "분위기", "mood", "톤", "tone"],
    "scene-extension": ["씬", "scene", "장면", "확장", "extension", "연장", "이어서", "continue"],
    "anime-mv": ["애니", "anime", "뮤비", "mv", "music video", "애니메이션", "animation", "오프닝", "opening"],
}


def recommend_workflow(prompt: str, ip_slug: str) -> str:
    """프롬프트와 IP slug 기반으로 워크플로우 추천.

    키워드 매칭으로 가장 적합한 워크플로우 템플릿을 선택합니다.
    """
    prompt_lower = prompt.lower() if prompt else ""
    ip_lower = ip_slug.lower() if ip_slug else ""

    # IP slug 기반 기본 추천
    if "anime" in ip_lower or "mv" in ip_lower or "cooking" in ip_lower:
        return "anime-mv"
    if "umbrella" in ip_lower or "shortform" in ip_lower:
        return "character-variation"

    # 프롬프트 키워드 매칭
    max_score = 0
    best_workflow = "character-variation"  # Default

    for workflow_key, keywords in KEYWORD_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > max_score:
            max_score = score
            best_workflow = workflow_key

    return best_workflow


# =============================================================================
# Pydantic Schemas
# =============================================================================

class GenerateDemoRequest(BaseModel):
    """Demo generation request."""
    prompt: Optional[str] = Field(None, max_length=2000, description="User prompt for workflow recommendation")
    preset_id: Optional[str] = Field(None, description="Optional preset ID (ignored in demo)")


class WorkflowStep(BaseModel):
    """Workflow step definition."""
    app: str
    href: str
    badge: str
    name_ko: str
    name_en: str


class GenerateDemoResponse(BaseModel):
    """Demo generation response with workflow recommendation."""
    generation_id: str
    workflow_key: str
    workflow_name_ko: str
    workflow_name_en: str
    workflow_steps: list[WorkflowStep]
    redirect_url: str
    message: str


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/{slug}/generate-demo", response_model=GenerateDemoResponse)
async def generate_demo(
    slug: str,
    request: GenerateDemoRequest,
):
    """데모용 워크플로우 추천 엔드포인트.

    실제 생성 없이 프롬프트 분석 → 워크플로우 추천 → 리다이렉트 URL 반환.
    투자자 데모 시연 후 삭제 예정.
    """
    prompt = request.prompt or ""

    # Recommend workflow based on prompt and IP slug
    workflow_key = recommend_workflow(prompt, slug)
    workflow_template = WORKFLOW_TEMPLATES.get(workflow_key, WORKFLOW_TEMPLATES["character-variation"])

    # Get first step for redirect
    first_step = workflow_template["steps"][0]

    # Build redirect URL with query params
    redirect_url = f"{first_step['href']}?ip={slug}"
    if prompt:
        # URL encode the prompt
        encoded_prompt = prompt.replace(" ", "+")[:100]  # Limit length
        redirect_url += f"&prompt={encoded_prompt}"

    # Generate unique ID for tracking
    generation_id = str(uuid4())

    logger.info(f"Demo workflow recommended: ip={slug}, workflow={workflow_key}, generation_id={generation_id}")

    return GenerateDemoResponse(
        generation_id=generation_id,
        workflow_key=workflow_key,
        workflow_name_ko=workflow_template["name_ko"],
        workflow_name_en=workflow_template["name_en"],
        workflow_steps=[WorkflowStep(**step) for step in workflow_template["steps"]],
        redirect_url=redirect_url,
        message="Workflow recommended. Click confirm to start.",
    )


@router.get("/{slug}/workflows")
async def get_available_workflows(slug: str):
    """Get available workflow templates for an IP.

    데모용: 모든 워크플로우 템플릿 반환.
    """
    # For demo, return all templates with IP-specific ordering
    ip_lower = slug.lower()

    # Determine recommended workflow
    if "anime" in ip_lower or "mv" in ip_lower or "cooking" in ip_lower:
        recommended = "anime-mv"
    elif "umbrella" in ip_lower or "shortform" in ip_lower:
        recommended = "character-variation"
    else:
        recommended = "character-variation"

    workflows = []
    for key, template in WORKFLOW_TEMPLATES.items():
        workflows.append({
            "key": key,
            "name_ko": template["name_ko"],
            "name_en": template["name_en"],
            "step_count": len(template["steps"]),
            "is_recommended": key == recommended,
            "steps": template["steps"],
        })

    # Sort with recommended first
    workflows.sort(key=lambda w: (0 if w["is_recommended"] else 1, w["key"]))

    return {
        "ip_slug": slug,
        "recommended_workflow": recommended,
        "workflows": workflows,
    }
