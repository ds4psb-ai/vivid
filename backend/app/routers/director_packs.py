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
    operator: str = Field(..., description="Comparison operator: eq, gt, lt, gte, lte, <=, >=, between, in, exists")
    value: Any
    tolerance: Optional[float] = None
    unit: Optional[str] = None


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
    """Create default DirectorPack for Bong Joon-ho style."""
    pack_id = "dp_bong_default"
    return DirectorPack(
        meta=PackMeta(
            pack_id=pack_id,
            pattern_id="auteur.bong-joon-ho",
            version="1.0.0",
            compiled_at=datetime.utcnow().isoformat(),
            compiled_by="system",
            invariant_count=5,
            slot_count=4,
            forbidden_count=3,
            checkpoint_count=6,
        ),
        dna_invariants=[
            DNAInvariant(
                rule_id="hook_timing_2s",
                rule_type="timing",
                name="훅 타이밍 2초",
                description="시청자 관심을 2초 이내에 사로잡기",
                condition="hook_punch_time",
                spec=RuleSpec(operator="<=", value=2.0),
                priority="critical",
                confidence=0.95,
                coach_line_ko="훅이 너무 늦어요! 시작하자마자 치고 나가세요.",
            ),
            DNAInvariant(
                rule_id="center_composition",
                rule_type="composition",
                name="중앙 구도",
                description="주요 피사체 중앙 배치",
                condition="center_offset",
                spec=RuleSpec(operator="<=", value=0.3),
                priority="high",
                confidence=0.88,
                coach_line_ko="피사체를 중앙으로 모아주세요!",
            ),
            DNAInvariant(
                rule_id="vertical_blocking",
                rule_type="composition",
                name="수직 블로킹",
                description="봉준호 스타일의 수직적 공간 활용",
                condition="vertical_depth",
                spec=RuleSpec(operator=">=", value=0.6),
                priority="high",
                confidence=0.82,
                coach_line_ko="위아래 공간을 더 활용하세요!",
            ),
            DNAInvariant(
                rule_id="cut_frequency",
                rule_type="timing",
                name="컷 빈도",
                description="적절한 컷 전환 속도 유지",
                condition="cuts_per_second",
                spec=RuleSpec(operator="<=", value=0.5),
                priority="medium",
                confidence=0.75,
                coach_line_ko="컷이 너무 빨라요. 좀 더 여유를 가지세요.",
            ),
            DNAInvariant(
                rule_id="audio_clarity",
                rule_type="audio",
                name="음성 명료도",
                description="대사가 명확하게 들리도록",
                condition="speech_clarity",
                spec=RuleSpec(operator=">=", value=0.8),
                priority="high",
                confidence=0.9,
                coach_line_ko="목소리가 잘 안 들려요! 마이크 확인!",
            ),
        ],
        mutation_slots=[
            MutationSlot(
                slot_id="opening_tone",
                slot_type="tone",
                name="오프닝 톤",
                description="씬 시작 분위기",
                allowed_values=["활기찬", "시니컬", "진지한", "친근한"],
                default_value="활기찬",
            ),
            MutationSlot(
                slot_id="camera_style",
                slot_type="style",
                name="카메라 스타일",
                allowed_values=["클로즈업", "미디엄", "와이드", "극단적 와이드"],
                default_value="미디엄",
            ),
            MutationSlot(
                slot_id="color_grade",
                slot_type="color",
                name="컬러 그레이딩",
                allowed_values=["자연스러운", "영화적", "빈티지", "고대비"],
                default_value="영화적",
            ),
            MutationSlot(
                slot_id="pacing_speed",
                slot_type="pacing",
                name="편집 속도",
                allowed_range=[0.5, 2.0],
                default_value=1.0,
            ),
        ],
        forbidden_mutations=[
            ForbiddenMutation(
                mutation_id="jump_cut_abuse",
                name="점프컷 남용",
                description="불필요한 점프컷 사용 금지",
                forbidden_condition="jump_cuts > 3 per minute",
                severity="major",
                coach_line_ko="점프컷이 너무 많아요!",
            ),
            ForbiddenMutation(
                mutation_id="dutch_angle",
                name="더치 앵글 금지",
                description="기울어진 카메라 앵글 사용 금지",
                forbidden_condition="camera_tilt > 15deg",
                severity="major",
                coach_line_ko="카메라를 똑바로!",
            ),
            ForbiddenMutation(
                mutation_id="fast_zoom",
                name="빠른 줌 금지",
                description="급격한 줌 인/아웃 금지",
                forbidden_condition="zoom_speed > 2x",
                severity="minor",
                coach_line_ko="줌이 너무 빨라요!",
            ),
        ],
        checkpoints=[
            Checkpoint(checkpoint_id="cp_hook", t=2, active_rules=["hook_timing_2s"], coach_prompt_ko="훅 체크"),
            Checkpoint(checkpoint_id="cp_10s", t=10, active_rules=["center_composition"], coach_prompt_ko="10초 체크"),
            Checkpoint(checkpoint_id="cp_30s", t=30, active_rules=["vertical_blocking"], coach_prompt_ko="30초 체크"),
            Checkpoint(checkpoint_id="cp_60s", t=60, active_rules=["cut_frequency"], coach_prompt_ko="1분 체크"),
            Checkpoint(checkpoint_id="cp_90s", t=90, active_rules=["audio_clarity"], coach_prompt_ko="1분 30초 체크"),
            Checkpoint(checkpoint_id="cp_end", t=120, active_rules=["center_composition", "audio_clarity"], coach_prompt_ko="마무리 체크"),
        ],
        policy=Policy(
            interrupt_on_violation=False,
            suggest_on_medium=True,
            language="ko",
        ),
        runtime_contract=RuntimeContract(
            max_session_sec=180,
            checkpoint_interval_sec=30,
            enable_realtime_feedback=False,
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
