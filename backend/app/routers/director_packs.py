"""DirectorPack API Router

Endpoints for managing DirectorPack DNA configurations for multi-scene consistency.

Endpoints:
- GET /director-packs - List available packs
- GET /director-packs/{pack_id} - Get specific pack
- POST /director-packs - Create new pack from capsule
- POST /director-packs/compile - Compile pack from VDG analysis
- PATCH /director-packs/{pack_id} - Update pack
- DELETE /director-packs/{pack_id} - Delete pack
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import json
import hashlib

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/director-packs", tags=["director-packs"])


# =============================================================================
# Pydantic Models
# =============================================================================

class RuleSpec(BaseModel):
    operator: str = Field(..., description="Comparison operator: eq, gt, lt, gte, lte, <=, >=, between, in, exists, ~=, pattern")
    value: Any
    tolerance: Optional[float] = None
    unit: Optional[str] = None
    context_filter: Optional[List[str]] = Field(
        default=None, 
        description="Contexts where this rule applies, e.g. ['sequence_start', 'shortform_start']"
    )


class DNAInvariant(BaseModel):
    rule_id: str
    rule_type: str = Field(..., description="timing, composition, engagement, audio, narrative, technical")
    name: str
    description: Optional[str] = None
    condition: str
    spec: RuleSpec
    priority: str = Field("medium", description="critical, high, medium, low")
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    coach_line: Optional[str] = None
    coach_line_ko: Optional[str] = None


class MutationSlot(BaseModel):
    slot_id: str
    slot_type: str = Field(..., description="style, tone, pacing, color, music, text")
    name: str
    description: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    allowed_range: Optional[List[float]] = None
    default_value: Optional[Any] = None
    persona_presets: Optional[Dict[str, Any]] = None


class ForbiddenMutation(BaseModel):
    mutation_id: str
    name: str
    description: str
    forbidden_condition: str
    severity: str = Field("major", description="critical, major, minor")
    coach_line: Optional[str] = None
    coach_line_ko: Optional[str] = None


class Checkpoint(BaseModel):
    checkpoint_id: str
    t: float
    active_rules: Optional[List[str]] = None
    check_rule_ids: Optional[List[str]] = None
    coach_prompt: Optional[str] = None
    coach_prompt_ko: Optional[str] = None


class Policy(BaseModel):
    interrupt_on_violation: bool = False
    suggest_on_medium: bool = True
    language: str = "ko"
    one_command_only: bool = False
    cooldown_sec: float = 3.0


class RuntimeContract(BaseModel):
    max_session_sec: int = 180
    checkpoint_interval_sec: int = 30
    enable_realtime_feedback: bool = False
    enable_audio_coach: bool = False


class PackMeta(BaseModel):
    pack_id: str
    pattern_id: str
    version: str = "1.0.0"
    source_vdg_id: Optional[str] = None
    compiled_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    compiled_by: Optional[str] = None
    invariant_count: int = 0
    slot_count: int = 0
    forbidden_count: int = 0
    checkpoint_count: int = 0


class DirectorPack(BaseModel):
    meta: PackMeta
    dna_invariants: List[DNAInvariant] = Field(default_factory=list)
    mutation_slots: List[MutationSlot] = Field(default_factory=list)
    forbidden_mutations: List[ForbiddenMutation] = Field(default_factory=list)
    checkpoints: List[Checkpoint] = Field(default_factory=list)
    policy: Policy = Field(default_factory=Policy)
    runtime_contract: RuntimeContract = Field(default_factory=RuntimeContract)


class DirectorPackCreate(BaseModel):
    pattern_id: str = Field(..., description="Capsule pattern ID (e.g., auteur.bong-joon-ho)")
    source_vdg_id: Optional[str] = None
    dna_invariants: Optional[List[DNAInvariant]] = None
    mutation_slots: Optional[List[MutationSlot]] = None
    forbidden_mutations: Optional[List[ForbiddenMutation]] = None
    checkpoints: Optional[List[Checkpoint]] = None
    policy: Optional[Policy] = None


class DirectorPackUpdate(BaseModel):
    dna_invariants: Optional[List[DNAInvariant]] = None
    mutation_slots: Optional[List[MutationSlot]] = None
    forbidden_mutations: Optional[List[ForbiddenMutation]] = None
    checkpoints: Optional[List[Checkpoint]] = None
    policy: Optional[Policy] = None


class CompileRequest(BaseModel):
    capsule_id: str
    vdg_content_id: Optional[str] = None
    use_defaults: bool = True


# =============================================================================
# In-Memory Store (replace with DB in production)
# =============================================================================

_pack_store: Dict[str, DirectorPack] = {}


def _generate_pack_id(pattern_id: str) -> str:
    """Generate unique pack ID from pattern ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    hash_suffix = hashlib.md5(f"{pattern_id}{timestamp}".encode()).hexdigest()[:6]
    return f"dp_{pattern_id.replace('.', '_')}_{hash_suffix}"


# =============================================================================
# Default Packs (pre-loaded)
# =============================================================================

def _create_default_bong_pack() -> DirectorPack:
    """Create default DirectorPack for Bong Joon-ho style.
    
    Based on extracted patterns from:
    - logic_rules.json (4 core patterns)
    - parasite_youtube_analysis.json
    - Film analysis databases
    
    15 DNA invariants covering:
    - Timing (4): hook, shot length, cut density, tempo
    - Composition (5): center, vertical, symmetry, depth, framing
    - Camera (3): controlled motion, deep focus, steadicam
    - Color/Light (2): natural light, motivated lighting
    - Audio (1): speech clarity
    """
    pack_id = "dp_bong_default"
    return DirectorPack(
        meta=PackMeta(
            pack_id=pack_id,
            pattern_id="auteur.bong-joon-ho",
            version="2.1.0",
            compiled_at=datetime.utcnow().isoformat(),
            compiled_by="system",
            invariant_count=17,
            slot_count=5,
            forbidden_count=5,
            checkpoint_count=8,
        ),
        dna_invariants=[
            # =================================================================
            # TIMING RULES (6)
            # =================================================================
            DNAInvariant(
                rule_id="hook_timing_1_5s",
                rule_type="timing",
                name="황금 1.5초 훅",
                description="시퀀스/숏폼 시작 시 1.5초 이내 시선 잡기 (컨텍스트 인식)",
                condition="hook_punch_time",
                spec=RuleSpec(
                    operator="<=",
                    value=1.5,
                    unit="sec",
                    context_filter=["sequence_start", "shortform_start", "cold_open"],
                ),
                priority="critical",
                confidence=0.95,
                coach_line_ko="1.5초! 시작부터 치고 나가세요!",
            ),
            DNAInvariant(
                rule_id="attention_refresh_2s",
                rule_type="timing",
                name="주의 환기 2초",
                description="씬 중간에서 주의력 환기 (mid-sequence용)",
                condition="attention_refresh_time",
                spec=RuleSpec(
                    operator="<=",
                    value=2.0,
                    unit="sec",
                    context_filter=["mid_sequence", "act_transition"],
                ),
                priority="medium",
                confidence=0.80,
                coach_line_ko="지루해지기 전에 새로운 자극을!",
            ),
            DNAInvariant(
                rule_id="expectation_fulfillment_10s",
                rule_type="engagement",
                name="10초 기대감 충족",
                description="훅에서 만든 기대감을 10초 내 부분 충족",
                condition="expectation_gap_closed",
                spec=RuleSpec(operator=">=", value=0.7),
                priority="high",
                confidence=0.82,
                coach_line_ko="10초까지 뭔가 보여줘야 해요!",
            ),
            DNAInvariant(
                rule_id="shot_length_median",
                rule_type="timing",
                name="샷 길이 중앙값 3.2초",
                description="3.2초 샷 길이 중앙값으로 느린 빌드업, 급격한 가속 패턴 구축",
                condition="median_shot_length",
                spec=RuleSpec(operator="~=", value=3.2, unit="sec", tolerance=0.5),
                priority="high",
                confidence=0.88,
                coach_line_ko="샷이 너무 짧아요. 봉준호 리듬을 느껴보세요.",
            ),
            DNAInvariant(
                rule_id="cut_frequency_controlled",
                rule_type="timing",
                name="컷 빈도 제어",
                description="서사 단계별 컷 밀도 차등 적용 (Hook 0.3 → Climax 3.5)",
                condition="cuts_per_second",
                spec=RuleSpec(operator="<=", value=0.5),
                priority="medium",
                confidence=0.75,
                coach_line_ko="컷이 너무 빨라요. 좀 더 여유를 가지세요.",
            ),
            DNAInvariant(
                rule_id="tempo_slow_build",
                rule_type="timing",
                name="느린 빌드업 템포",
                description="초반 느린 빌드업 후 급격히 가속되는 시간적 리듬",
                condition="tempo_acceleration",
                spec=RuleSpec(operator="pattern", value="slow_build_rapid_acceleration"),
                priority="high",
                confidence=0.82,
                coach_line_ko="처음부터 너무 급해요. 천천히 쌓아올리세요.",
            ),
            # =================================================================
            # COMPOSITION RULES (5)
            # =================================================================
            DNAInvariant(
                rule_id="center_composition",
                rule_type="composition",
                name="중앙 대칭 구도",
                description="주요 피사체 중앙 배치, 대칭성 점수 0.74 이상",
                condition="center_offset",
                spec=RuleSpec(operator="<=", value=0.3),
                priority="high",
                confidence=0.88,
                coach_line_ko="피사체를 중앙으로 모아주세요!",
            ),
            DNAInvariant(
                rule_id="vertical_blocking",
                rule_type="composition",
                name="수직 블로킹 (계급 시각화)",
                description="프레임 내 수직적 위치로 사회적 권력 관계 표현 (위=부유, 아래=빈곤)",
                condition="vertical_depth",
                spec=RuleSpec(operator=">=", value=0.6),
                priority="critical",
                confidence=0.90,
                coach_line_ko="위아래 공간을 활용해 계급을 표현하세요!",
            ),
            DNAInvariant(
                rule_id="horizontal_class_coding",
                rule_type="composition",
                name="수평 계급 코딩",
                description="화면 좌측=빈곤, 우측=부유의 수평적 계급 배치",
                condition="horizontal_class_position",
                spec=RuleSpec(operator="pattern", value="left_poverty_right_wealth"),
                priority="medium",
                confidence=0.74,
                coach_line_ko="좌우 배치로 계급 차이를 암시하세요.",
            ),
            DNAInvariant(
                rule_id="staircase_diagonal",
                rule_type="composition",
                name="계단 대각선 모티프",
                description="계단과 대각선을 통한 계급 이동/상승/하락 시각화",
                condition="diagonal_elements",
                spec=RuleSpec(operator="exists", value=True),
                priority="high",
                confidence=0.86,
                coach_line_ko="계단이나 대각선 요소를 넣어보세요!",
            ),
            DNAInvariant(
                rule_id="window_frame_in_frame",
                rule_type="composition",
                name="창문 프레임 인 프레임",
                description="창문, 문, 통로를 통한 자연스러운 프레이밍 활용",
                condition="frame_within_frame",
                spec=RuleSpec(operator="exists", value=True),
                priority="medium",
                confidence=0.78,
                coach_line_ko="창문이나 문을 프레임으로 활용해보세요.",
            ),
            # =================================================================
            # CAMERA RULES (3)
            # =================================================================
            DNAInvariant(
                rule_id="controlled_camera_80",
                rule_type="camera",
                name="80% 통제된 카메라",
                description="평상시 80% 이상 정적/돌리 촬영, 감정 폭발 시에만 핸드헬드",
                condition="controlled_motion_ratio",
                spec=RuleSpec(operator=">=", value=0.8),
                priority="critical",
                confidence=0.92,
                coach_line_ko="카메라를 더 안정적으로! 핸드헬드는 아껴두세요.",
            ),
            DNAInvariant(
                rule_id="deep_focus_preference",
                rule_type="camera",
                name="딥 포커스 선호",
                description="전경/중경/후경 모두 선명하게 유지하는 딥 포커스 촬영",
                condition="focus_depth",
                spec=RuleSpec(operator="==", value="deep"),
                priority="high",
                confidence=0.85,
                coach_line_ko="포커스를 깊게! 배경도 중요해요.",
            ),
            DNAInvariant(
                rule_id="dolly_over_zoom",
                rule_type="camera",
                name="줌 대신 돌리",
                description="줌 대신 돌리 무브먼트 사용 (35% 돌리 비율)",
                condition="dolly_usage",
                spec=RuleSpec(operator=">=", value=0.3),
                priority="medium",
                confidence=0.78,
                coach_line_ko="줌 말고 카메라를 직접 움직이세요!",
            ),
            # =================================================================
            # LIGHTING RULES (2)
            # =================================================================
            DNAInvariant(
                rule_id="natural_light_motivated",
                rule_type="lighting",
                name="동기화된 자연광",
                description="창문, 문을 통해 들어오는 동기화된 자연광 활용",
                condition="motivated_lighting",
                spec=RuleSpec(operator="exists", value=True),
                priority="medium",
                confidence=0.80,
                coach_line_ko="조명이 어디서 오는지 보여주세요.",
            ),
            DNAInvariant(
                rule_id="practical_light_use",
                rule_type="lighting",
                name="실용광 활용",
                description="장면 내 램프, 창문광 등 실용광을 조명으로 활용",
                condition="practical_lights",
                spec=RuleSpec(operator=">=", value=1),
                priority="low",
                confidence=0.72,
                coach_line_ko="장면 안의 조명(램프 등)을 활용해보세요.",
            ),
            # =================================================================
            # AUDIO RULES (1)
            # =================================================================
            DNAInvariant(
                rule_id="audio_clarity",
                rule_type="audio",
                name="음성 명료도",
                description="대사가 명확하게 들리도록 음성 클리어런스 확보",
                condition="speech_clarity",
                spec=RuleSpec(operator=">=", value=0.8),
                priority="high",
                confidence=0.90,
                coach_line_ko="목소리가 잘 안 들려요! 마이크 확인!",
            ),
        ],
        mutation_slots=[
            MutationSlot(
                slot_id="opening_tone",
                slot_type="tone",
                name="오프닝 톤",
                description="씬 시작 분위기 (봉준호 특유의 유머와 긴장의 공존)",
                allowed_values=["블랙코미디", "시니컬", "일상적", "긴장감", "유머러스"],
                default_value="블랙코미디",
            ),
            MutationSlot(
                slot_id="camera_position",
                slot_type="style",
                name="카메라 위치",
                description="봉준호 스타일 카메라 높이",
                allowed_values=["로우앵글", "아이레벨", "하이앵글", "버즈아이"],
                default_value="아이레벨",
            ),
            MutationSlot(
                slot_id="color_grade",
                slot_type="color",
                name="컬러 그레이딩",
                description="기생충 스타일 컬러 팔레트",
                allowed_values=["자연스러운", "영화적", "차가운톤", "따뜻한톤", "로우새추레이션"],
                default_value="영화적",
            ),
            MutationSlot(
                slot_id="pacing_speed",
                slot_type="pacing",
                name="편집 속도",
                description="서사 단계별 페이싱 속도 배율",
                allowed_range=[0.5, 2.0],
                default_value=1.0,
            ),
            MutationSlot(
                slot_id="narrative_stage",
                slot_type="narrative",
                name="서사 단계",
                description="현재 씬의 서사 위치",
                allowed_values=["Hook", "Build", "Turn", "Payoff", "Climax"],
                default_value="Build",
            ),
        ],
        forbidden_mutations=[
            ForbiddenMutation(
                mutation_id="jump_cut_abuse",
                name="점프컷 남용",
                description="불필요한 점프컷 사용 금지 (분당 3회 초과 금지)",
                forbidden_condition="jump_cuts > 3 per minute",
                severity="major",
                coach_line_ko="점프컷이 너무 많아요!",
            ),
            ForbiddenMutation(
                mutation_id="dutch_angle",
                name="더치 앵글 금지",
                description="기울어진 카메라 앵글 사용 금지 (봉준호 스타일에 맞지 않음)",
                forbidden_condition="camera_tilt > 15deg",
                severity="critical",
                coach_line_ko="카메라를 똑바로! 봉준호는 수평을 지켜요.",
            ),
            ForbiddenMutation(
                mutation_id="fast_zoom",
                name="빠른 줌 금지",
                description="급격한 줌 인/아웃 금지 (돌리로 대체)",
                forbidden_condition="zoom_speed > 2x",
                severity="major",
                coach_line_ko="줌 대신 돌리를 쓰세요!",
            ),
            ForbiddenMutation(
                mutation_id="shaky_cam_abuse",
                name="핸드헬드 남용 금지",
                description="핸드헬드 촬영은 감정 폭발 시에만 15% 이하",
                forbidden_condition="handheld_ratio > 0.2",
                severity="major",
                coach_line_ko="핸드헬드는 아껴두세요! 감정 폭발용이에요.",
            ),
            ForbiddenMutation(
                mutation_id="shallow_focus_abuse",
                name="얕은 심도 남용 금지",
                description="배경 블러 과도 사용 금지 (딥 포커스 선호)",
                forbidden_condition="shallow_focus_ratio > 0.3",
                severity="minor",
                coach_line_ko="배경도 보여주세요! 딥 포커스로!",
            ),
        ],
        checkpoints=[
            Checkpoint(checkpoint_id="cp_hook", t=2, active_rules=["hook_timing_2s"], coach_prompt_ko="훅 체크 - 2초 안에 잡았나?"),
            Checkpoint(checkpoint_id="cp_5s", t=5, active_rules=["vertical_blocking", "center_composition"], coach_prompt_ko="5초 구도 체크"),
            Checkpoint(checkpoint_id="cp_10s", t=10, active_rules=["controlled_camera_80"], coach_prompt_ko="10초 카메라 안정성 체크"),
            Checkpoint(checkpoint_id="cp_20s", t=20, active_rules=["deep_focus_preference", "natural_light_motivated"], coach_prompt_ko="20초 조명/포커스 체크"),
            Checkpoint(checkpoint_id="cp_30s", t=30, active_rules=["staircase_diagonal", "window_frame_in_frame"], coach_prompt_ko="30초 프레이밍 체크"),
            Checkpoint(checkpoint_id="cp_60s", t=60, active_rules=["shot_length_median", "tempo_slow_build"], coach_prompt_ko="1분 리듬 체크"),
            Checkpoint(checkpoint_id="cp_90s", t=90, active_rules=["audio_clarity", "cut_frequency_controlled"], coach_prompt_ko="1분 30초 오디오/컷 체크"),
            Checkpoint(checkpoint_id="cp_end", t=120, active_rules=["vertical_blocking", "controlled_camera_80", "audio_clarity"], coach_prompt_ko="마무리 종합 체크"),
        ],
        policy=Policy(
            interrupt_on_violation=False,
            suggest_on_medium=True,
            language="ko",
            one_command_only=True,
            cooldown_sec=2.5,
        ),
        runtime_contract=RuntimeContract(
            max_session_sec=180,
            checkpoint_interval_sec=20,
            enable_realtime_feedback=True,
            enable_audio_coach=False,
        ),
    )


# Initialize default packs
def _init_default_packs():
    bong_pack = _create_default_bong_pack()
    _pack_store[bong_pack.meta.pack_id] = bong_pack


_init_default_packs()


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/")
async def list_director_packs(
    pattern_id: Optional[str] = Query(None, description="Filter by pattern ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """List available DirectorPacks.
    
    Returns:
        List of DirectorPack summaries with pagination info.
    """
    packs = list(_pack_store.values())
    
    # Filter by pattern_id if provided
    if pattern_id:
        packs = [p for p in packs if pattern_id in p.meta.pattern_id]
    
    total = len(packs)
    packs = packs[offset:offset + limit]
    
    return {
        "success": True,
        "data": [
            {
                "pack_id": p.meta.pack_id,
                "pattern_id": p.meta.pattern_id,
                "version": p.meta.version,
                "compiled_at": p.meta.compiled_at,
                "invariant_count": len(p.dna_invariants),
                "slot_count": len(p.mutation_slots),
                "forbidden_count": len(p.forbidden_mutations),
            }
            for p in packs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{pack_id}")
async def get_director_pack(pack_id: str) -> Dict[str, Any]:
    """Get a specific DirectorPack by ID.
    
    Args:
        pack_id: DirectorPack identifier
        
    Returns:
        Full DirectorPack object.
    """
    pack = _pack_store.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"DirectorPack not found: {pack_id}")
    
    return {
        "success": True,
        "data": pack.model_dump(),
    }


@router.get("/by-pattern/{pattern_id}")
async def get_pack_by_pattern(pattern_id: str) -> Dict[str, Any]:
    """Get DirectorPack by pattern ID (e.g., auteur.bong-joon-ho).
    
    Returns the latest/default pack for the given pattern.
    """
    # Find packs matching pattern
    matching = [p for p in _pack_store.values() if pattern_id in p.meta.pattern_id]
    
    if not matching:
        raise HTTPException(status_code=404, detail=f"No DirectorPack found for pattern: {pattern_id}")
    
    # Return latest (or default if exists)
    pack = matching[0]
    for p in matching:
        if "default" in p.meta.pack_id:
            pack = p
            break
    
    return {
        "success": True,
        "data": pack.model_dump(),
    }


@router.post("/")
async def create_director_pack(request: DirectorPackCreate) -> Dict[str, Any]:
    """Create a new DirectorPack.
    
    Args:
        request: DirectorPack creation request with pattern_id and optional rules.
        
    Returns:
        Created DirectorPack.
    """
    pack_id = _generate_pack_id(request.pattern_id)
    
    pack = DirectorPack(
        meta=PackMeta(
            pack_id=pack_id,
            pattern_id=request.pattern_id,
            version="1.0.0",
            source_vdg_id=request.source_vdg_id,
            compiled_at=datetime.utcnow().isoformat(),
            invariant_count=len(request.dna_invariants or []),
            slot_count=len(request.mutation_slots or []),
            forbidden_count=len(request.forbidden_mutations or []),
            checkpoint_count=len(request.checkpoints or []),
        ),
        dna_invariants=request.dna_invariants or [],
        mutation_slots=request.mutation_slots or [],
        forbidden_mutations=request.forbidden_mutations or [],
        checkpoints=request.checkpoints or [],
        policy=request.policy or Policy(),
        runtime_contract=RuntimeContract(),
    )
    
    _pack_store[pack_id] = pack
    logger.info(f"Created DirectorPack: {pack_id} for pattern {request.pattern_id}")
    
    return {
        "success": True,
        "data": pack.model_dump(),
        "message": f"DirectorPack created: {pack_id}",
    }


@router.post("/compile")
async def compile_director_pack(request: CompileRequest) -> Dict[str, Any]:
    """Compile a DirectorPack from a capsule.
    
    This endpoint generates a DirectorPack based on the capsule's auteur style
    and optionally incorporates VDG analysis results.
    
    Args:
        request: Compile request with capsule_id and options.
        
    Returns:
        Compiled DirectorPack.
    """
    # For now, use default packs based on capsule_id
    if "bong" in request.capsule_id.lower():
        pack = _create_default_bong_pack()
        # Generate new ID for the compiled pack
        pack.meta.pack_id = _generate_pack_id(request.capsule_id)
        pack.meta.source_vdg_id = request.vdg_content_id
        _pack_store[pack.meta.pack_id] = pack
        
        return {
            "success": True,
            "data": pack.model_dump(),
            "message": f"Compiled DirectorPack from {request.capsule_id}",
        }
    
    # TODO: Implement actual compilation from VDG when available
    raise HTTPException(
        status_code=501,
        detail=f"Compilation not yet supported for capsule: {request.capsule_id}. Use 'bong' capsules for now.",
    )


@router.patch("/{pack_id}")
async def update_director_pack(
    pack_id: str,
    update: DirectorPackUpdate,
) -> Dict[str, Any]:
    """Update an existing DirectorPack.
    
    Args:
        pack_id: DirectorPack identifier
        update: Fields to update
        
    Returns:
        Updated DirectorPack.
    """
    pack = _pack_store.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"DirectorPack not found: {pack_id}")
    
    # Update fields
    if update.dna_invariants is not None:
        pack.dna_invariants = update.dna_invariants
        pack.meta.invariant_count = len(update.dna_invariants)
    
    if update.mutation_slots is not None:
        pack.mutation_slots = update.mutation_slots
        pack.meta.slot_count = len(update.mutation_slots)
    
    if update.forbidden_mutations is not None:
        pack.forbidden_mutations = update.forbidden_mutations
        pack.meta.forbidden_count = len(update.forbidden_mutations)
    
    if update.checkpoints is not None:
        pack.checkpoints = update.checkpoints
        pack.meta.checkpoint_count = len(update.checkpoints)
    
    if update.policy is not None:
        pack.policy = update.policy
    
    # Update version
    version_parts = pack.meta.version.split(".")
    version_parts[-1] = str(int(version_parts[-1]) + 1)
    pack.meta.version = ".".join(version_parts)
    
    _pack_store[pack_id] = pack
    logger.info(f"Updated DirectorPack: {pack_id} to version {pack.meta.version}")
    
    return {
        "success": True,
        "data": pack.model_dump(),
        "message": f"DirectorPack updated to version {pack.meta.version}",
    }


@router.delete("/{pack_id}")
async def delete_director_pack(pack_id: str) -> Dict[str, Any]:
    """Delete a DirectorPack.
    
    Note: Default packs cannot be deleted.
    
    Args:
        pack_id: DirectorPack identifier
        
    Returns:
        Deletion confirmation.
    """
    if "default" in pack_id:
        raise HTTPException(status_code=403, detail="Cannot delete default DirectorPacks")
    
    pack = _pack_store.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"DirectorPack not found: {pack_id}")
    
    del _pack_store[pack_id]
    logger.info(f"Deleted DirectorPack: {pack_id}")
    
    return {
        "success": True,
        "message": f"DirectorPack deleted: {pack_id}",
    }


@router.get("/{pack_id}/export")
async def export_director_pack(pack_id: str) -> Dict[str, Any]:
    """Export DirectorPack as JSON for external use.
    
    Returns:
        DirectorPack in exportable format.
    """
    pack = _pack_store.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"DirectorPack not found: {pack_id}")
    
    return {
        "success": True,
        "data": pack.model_dump(),
        "export_format": "json",
        "exported_at": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Validation Endpoints
# =============================================================================

class ShotContract(BaseModel):
    """Shot contract for validation."""
    shot_id: str
    prompt: Optional[str] = None
    visual_prompt: Optional[str] = None
    duration_sec: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    cuts_per_second: Optional[float] = None


class ValidateRequest(BaseModel):
    """Request for DNA compliance validation."""
    pack_id: str
    shots: List[ShotContract]


class RuleResult(BaseModel):
    """Result of a single rule check."""
    rule_id: str
    rule_name: str
    priority: str
    level: str
    confidence: float
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


class ShotReportResponse(BaseModel):
    """Compliance report for a single shot."""
    shot_id: str
    overall_level: str
    overall_confidence: float
    rule_results: List[RuleResult]
    critical_violations: int
    high_violations: int
    suggestions: List[str]


class BatchReportResponse(BaseModel):
    """Compliance report for batch validation."""
    total_shots: int
    compliant_shots: int
    partial_shots: int
    violation_shots: int
    overall_compliance_rate: float
    summary: str
    shot_reports: List[ShotReportResponse]


@router.post("/validate")
async def validate_shots(request: ValidateRequest) -> Dict[str, Any]:
    """Validate shot contracts against DirectorPack DNA rules.
    
    Args:
        request: Validation request with pack_id and shots
        
    Returns:
        BatchComplianceReport with per-shot details and summary
    """
    from app.services.dna_validator import (
        validate_batch_compliance,
        ComplianceLevel,
    )
    
    pack = _pack_store.get(request.pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"DirectorPack not found: {request.pack_id}")
    
    # Convert shots to dicts for validator
    shots_dict = [shot.model_dump() for shot in request.shots]
    pack_dict = pack.model_dump()
    
    # Run validation
    report = validate_batch_compliance(shots_dict, pack_dict)
    
    # Convert to response format
    shot_reports = []
    for sr in report.shot_reports:
        shot_reports.append(ShotReportResponse(
            shot_id=sr.shot_id,
            overall_level=sr.overall_level.value,
            overall_confidence=sr.overall_confidence,
            rule_results=[
                RuleResult(
                    rule_id=r.rule_id,
                    rule_name=r.rule_name,
                    priority=r.priority.value,
                    level=r.level.value,
                    confidence=r.confidence,
                    message=r.message,
                    expected=r.expected,
                    actual=r.actual,
                )
                for r in sr.rule_results
            ],
            critical_violations=sr.critical_violations,
            high_violations=sr.high_violations,
            suggestions=sr.suggestions,
        ))
    
    return {
        "success": True,
        "data": {
            "total_shots": report.total_shots,
            "compliant_shots": report.compliant_shots,
            "partial_shots": report.partial_shots,
            "violation_shots": report.violation_shots,
            "overall_compliance_rate": report.overall_compliance_rate,
            "summary": report.summary,
            "shot_reports": [sr.model_dump() for sr in shot_reports],
        },
        "pack_id": request.pack_id,
        "validated_at": datetime.utcnow().isoformat(),
    }


@router.post("/{pack_id}/validate-single")
async def validate_single_shot(
    pack_id: str,
    shot: ShotContract,
) -> Dict[str, Any]:
    """Validate a single shot contract against DirectorPack DNA rules.
    
    Args:
        pack_id: DirectorPack identifier
        shot: Shot contract to validate
        
    Returns:
        ShotComplianceReport with rule-by-rule details
    """
    from app.services.dna_validator import (
        validate_shot_compliance,
        get_compliance_badge,
    )
    
    pack = _pack_store.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"DirectorPack not found: {pack_id}")
    
    shot_dict = shot.model_dump()
    pack_dict = pack.model_dump()
    
    report = validate_shot_compliance(shot_dict, pack_dict)
    badge = get_compliance_badge(report.overall_level)
    
    return {
        "success": True,
        "data": {
            "shot_id": report.shot_id,
            "badge": badge,
            "overall_level": report.overall_level.value,
            "overall_confidence": report.overall_confidence,
            "critical_violations": report.critical_violations,
            "high_violations": report.high_violations,
            "suggestions": report.suggestions,
            "rule_results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "priority": r.priority.value,
                    "level": r.level.value,
                    "confidence": r.confidence,
                    "message": r.message,
                    "expected": r.expected,
                    "actual": r.actual,
                }
                for r in report.rule_results
            ],
        },
        "pack_id": pack_id,
        "validated_at": datetime.utcnow().isoformat(),
    }

