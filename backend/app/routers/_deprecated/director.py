"""
Director Router - AI 총감독 API

바이브 코딩 인터페이스의 백엔드 API를 제공합니다.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.director import (
    director_agent,
    VibeInput,
    WorkflowPlan,
    NarrativeDNA,
    VibePreset,
    VIBE_PRESETS,
)
from app.logging_config import get_logger

router = APIRouter(prefix="/director", tags=["director"])
logger = get_logger("director_router")


class VibeInterpretRequest(BaseModel):
    """바이브 해석 요청"""
    type: str  # 'preset' | 'custom'
    preset_id: Optional[str] = None
    custom_description: Optional[str] = None
    output_type: str = "short_drama"
    target_length_sec: int = 60
    capsule_id: Optional[str] = None  # e.g. 'auteur.bong-joon-ho'


class VibeInterpretResponse(BaseModel):
    """바이브 해석 응답"""
    workflow_id: str
    nodes: List[dict]
    edges: List[dict]
    narrative_dna: dict
    estimated_duration_sec: int
    agent_assignments: dict
    capsule_id: Optional[str] = None
    logic_vector: Optional[dict] = None
    persona_vector: Optional[dict] = None


class PresetListResponse(BaseModel):
    """프리셋 목록 응답"""
    presets: List[dict]


@router.get("/presets", response_model=PresetListResponse)
async def list_presets() -> PresetListResponse:
    """
    사용 가능한 바이브 프리셋 목록을 반환합니다.
    """
    return PresetListResponse(
        presets=[preset.model_dump() for preset in VIBE_PRESETS.values()]
    )


@router.post("/interpret-vibe", response_model=VibeInterpretResponse)
async def interpret_vibe(request: VibeInterpretRequest) -> VibeInterpretResponse:
    """
    바이브 입력을 해석하여 워크플로우 계획을 생성합니다.
    
    - **preset 모드**: 사전 정의된 바이브 프리셋 사용
    - **custom 모드**: 자연어로 바이브 설명
    
    반환되는 워크플로우 계획에는:
    - 노드 목록과 위치
    - 엣지 연결 정보
    - 서사 DNA (톤, 스타일, 테마 등)
    - 에이전트 할당 정보
    """
    logger.info(
        "Vibe interpretation requested",
        extra={
            "type": request.type,
            "preset_id": request.preset_id,
            "output_type": request.output_type,
        }
    )
    
    try:
        vibe_input = VibeInput(
            type=request.type,
            preset_id=request.preset_id,
            custom_description=request.custom_description,
            output_type=request.output_type,
            target_length_sec=request.target_length_sec,
            capsule_id=request.capsule_id,
        )
        
        workflow = await director_agent.interpret_vibe(vibe_input)
        
        return VibeInterpretResponse(
            workflow_id=workflow.workflow_id,
            nodes=[node.model_dump() for node in workflow.nodes],
            edges=[edge.model_dump() for edge in workflow.edges],
            narrative_dna=workflow.narrative_dna.model_dump(),
            estimated_duration_sec=workflow.estimated_duration_sec,
            agent_assignments=workflow.agent_assignments,
            capsule_id=workflow.capsule_id,
            logic_vector=workflow.logic_vector,
            persona_vector=workflow.persona_vector,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Vibe interpretation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="워크플로우 생성에 실패했습니다")


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str) -> dict:
    """
    특정 프리셋의 상세 정보를 반환합니다.
    """
    preset = VIBE_PRESETS.get(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
    return preset.model_dump()


# --- DNA Compliance API ---

class ComplianceCheckRequest(BaseModel):
    """DNA 준수 검사 요청"""
    content: str
    content_type: str = "script"  # script, dialogue, description, visual
    narrative_dna: dict
    node_id: Optional[str] = None


class ComplianceCheckResponse(BaseModel):
    """DNA 준수 검사 응답"""
    content_id: str
    is_compliant: bool
    compliance_score: float
    issues: List[dict]
    suggestions: List[dict]


@router.post("/check-compliance", response_model=ComplianceCheckResponse)
async def check_compliance(request: ComplianceCheckRequest) -> ComplianceCheckResponse:
    """
    콘텐츠가 서사 DNA를 준수하는지 검사합니다.
    
    - **content**: 검사할 텍스트 (대본, 대사, 설명 등)
    - **content_type**: script, dialogue, description, visual
    - **narrative_dna**: 준수해야 할 DNA 정의
    
    반환:
    - 준수 여부 및 점수
    - 위반 이슈 목록
    - 개선 제안
    """
    from app.agents.dna_validator import dna_validator
    
    try:
        dna = NarrativeDNA(**request.narrative_dna)
        
        result = await dna_validator.check_compliance(
            content=request.content,
            content_type=request.content_type,
            dna=dna,
            node_id=request.node_id,
        )
        
        suggestions = await dna_validator.generate_suggestions(result)
        
        return ComplianceCheckResponse(
            content_id=result.content_id,
            is_compliant=result.is_compliant,
            compliance_score=result.compliance_score,
            issues=[issue.model_dump() for issue in result.issues],
            suggestions=suggestions,
        )
        
    except Exception as e:
        logger.error(f"Compliance check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="준수 검사에 실패했습니다")


# --- Foreshadow Analysis API ---

class ForeshadowRequest(BaseModel):
    """복선 분석 요청"""
    full_script: str
    segments: Optional[List[dict]] = None  # [{"label": "1막", "content": "..."}]


class ForeshadowResponse(BaseModel):
    """복선 분석 응답"""
    total_seeds: int
    resolved_seeds: int
    orphaned_seeds: List[dict]
    suggestions: List[dict]
    analysis_score: float


@router.post("/analyze-foreshadow", response_model=ForeshadowResponse)
async def analyze_foreshadow(request: ForeshadowRequest) -> ForeshadowResponse:
    """
    시나리오의 복선 설정 및 회수 여부를 분석합니다.
    
    1M 토큰 컨텍스트를 활용하여:
    - 설정된 복선(씨앗) 탐지
    - 회수(페이오프) 매칭
    - 미회수 복선에 대한 활용 제안
    """
    from app.agents.foreshadow_agent import foreshadow_agent
    
    try:
        result = await foreshadow_agent.analyze_narrative(
            full_script=request.full_script,
            segments=request.segments,
        )
        
        return ForeshadowResponse(
            total_seeds=result.total_seeds,
            resolved_seeds=result.resolved_seeds,
            orphaned_seeds=[s.model_dump() for s in result.orphaned_seeds],
            suggestions=result.suggestions,
            analysis_score=result.analysis_score,
        )
        
    except Exception as e:
        logger.error(f"Foreshadow analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="복선 분석에 실패했습니다")
