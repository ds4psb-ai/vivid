"""Standardized artifact schemas for Vivid.

Defines Pydantic models for all artifact types produced by the agent,
ensuring consistent structure for storyboards, shot lists, and data tables.
"""
from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.storyboard_utils import normalize_storyboard_cards

class ArtifactType(str, Enum):
    """Supported artifact types."""
    STORYBOARD = "storyboard"
    SHOT_LIST = "shot_list"
    DATA_TABLE = "data_table"
    SCENE_CARD = "scene_card"
    CONTI = "conti"
    VIDEO_SUMMARY = "video_summary"


class ShotType(str, Enum):
    """Standard shot types."""
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close-up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    OVERHEAD = "overhead"
    LOW_ANGLE = "low_angle"
    DUTCH = "dutch"
    POV = "pov"


# =============================================================================
# Storyboard Artifact
# =============================================================================

class StoryboardCard(BaseModel):
    """Single storyboard card representing one shot."""
    shot_id: str = Field(..., description="고유 샷 ID (예: shot-01-01)")
    shot_type: str = Field("medium", description="샷 유형 (wide, medium, close-up)")
    description: str = Field(..., description="샷 설명")
    composition: str = Field(..., description="구도 힌트")
    duration_sec: int = Field(4, ge=1, le=300, description="예상 길이 (초)")
    dominant_color: str = Field("#333333", description="주요 색상 (hex)")
    accent_color: str = Field("#555555", description="강조 색상 (hex)")
    note: Optional[str] = Field(None, description="추가 노트")
    evidence_refs: List[str] = Field(default_factory=list, description="증거 참조 목록")
    
    # Extended fields for production
    camera_movement: Optional[str] = Field(None, description="카메라 무빙 (pan, tilt, dolly)")
    audio_cue: Optional[str] = Field(None, description="오디오 큐")
    dialogue: Optional[str] = Field(None, description="대사")
    thumbnail_url: Optional[str] = Field(None, description="썸네일 이미지 URL")


class StoryboardArtifact(BaseModel):
    """Complete storyboard artifact."""
    artifact_type: str = Field(default=ArtifactType.STORYBOARD.value)
    artifact_id: str = Field(..., description="고유 아티팩트 ID")
    title: str = Field(..., description="스토리보드 제목")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Capsule context
    capsule_id: Optional[str] = Field(None, description="거장 스타일 ID")
    capsule_version: Optional[str] = Field(None, description="캡슐 버전")
    
    # Cards
    cards: List[StoryboardCard] = Field(default_factory=list, description="스토리보드 카드 목록")
    total_duration_sec: int = Field(0, description="총 예상 길이 (초)")
    
    # DNA context (from DirectorAgent)
    narrative_dna: Optional[Dict[str, Any]] = Field(None, description="서사 DNA")
    logic_vector: Optional[Dict[str, Any]] = Field(None, description="Logic Vector")
    persona_vector: Optional[Dict[str, Any]] = Field(None, description="Persona Vector")
    
    def model_post_init(self, __context: Any) -> None:
        """Calculate total duration if not set."""
        if self.cards and self.total_duration_sec == 0:
            self.total_duration_sec = sum(card.duration_sec for card in self.cards)


# =============================================================================
# Shot List Artifact
# =============================================================================

class ShotListItem(BaseModel):
    """Single shot list entry for production use."""
    shot_id: str = Field(..., description="샷 ID")
    sequence: str = Field(..., description="시퀀스 번호")
    scene: str = Field(..., description="씬 번호")
    shot_size: str = Field(..., description="샷 사이즈 (WS, MS, CU)")
    action: str = Field(..., description="액션 설명")
    dialogue: Optional[str] = Field(None, description="대사")
    duration: str = Field(..., description="예상 길이 (예: 3s)")
    notes: Optional[str] = Field(None, description="촬영 노트")
    
    # Production fields
    location: Optional[str] = Field(None, description="촬영 장소")
    props: Optional[List[str]] = Field(None, description="소품 목록")
    cast: Optional[List[str]] = Field(None, description="출연진")
    camera: Optional[str] = Field(None, description="카메라 설정")
    lighting: Optional[str] = Field(None, description="조명 설정")


class ShotListArtifact(BaseModel):
    """Complete shot list artifact for production."""
    artifact_type: str = Field(default=ArtifactType.SHOT_LIST.value)
    artifact_id: str = Field(..., description="고유 아티팩트 ID")
    title: str = Field(..., description="샷 리스트 제목")
    project_id: Optional[str] = Field(None, description="프로젝트 ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    shots: List[ShotListItem] = Field(default_factory=list, description="샷 목록")
    total_shots: int = Field(0, description="총 샷 수")
    
    def model_post_init(self, __context: Any) -> None:
        """Calculate total shots if not set."""
        if self.shots and self.total_shots == 0:
            self.total_shots = len(self.shots)


# =============================================================================
# Data Table Artifact (NotebookLM-style)
# =============================================================================

class DataTableColumn(BaseModel):
    """Column definition for data table."""
    id: str = Field(..., description="컬럼 ID")
    name: str = Field(..., description="컬럼 이름")
    type: str = Field("string", description="데이터 타입 (string, number, boolean, date)")
    description: Optional[str] = Field(None, description="컬럼 설명")


class DataTableArtifact(BaseModel):
    """Structured data table artifact (NotebookLM style).
    
    Used for organizing extracted insights, claims, and evidence
    in a tabular format that can be exported to Sheets.
    """
    artifact_type: str = Field(default=ArtifactType.DATA_TABLE.value)
    artifact_id: str = Field(..., description="고유 아티팩트 ID")
    title: str = Field(..., description="테이블 제목")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    columns: List[DataTableColumn] = Field(default_factory=list, description="컬럼 정의")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="데이터 행")
    
    # Provenance
    source_refs: List[str] = Field(default_factory=list, description="소스 참조 목록")
    capsule_id: Optional[str] = Field(None, description="생성에 사용된 캡슐 ID")
    
    @property
    def row_count(self) -> int:
        return len(self.rows)
    
    @property
    def column_count(self) -> int:
        return len(self.columns)


# =============================================================================
# Scene Card Artifact
# =============================================================================

class SceneCardArtifact(BaseModel):
    """Individual scene card, a simpler version of storyboard card."""
    artifact_type: str = Field(default=ArtifactType.SCENE_CARD.value)
    artifact_id: str = Field(..., description="고유 아티팩트 ID")
    scene_number: int = Field(..., description="씬 번호")
    title: str = Field(..., description="씬 제목")
    description: str = Field(..., description="씬 설명")
    
    # Visual
    mood: Optional[str] = Field(None, description="분위기")
    color_palette: List[str] = Field(default_factory=list, description="색상 팔레트")
    
    # Timing
    duration_sec: int = Field(5, description="예상 길이")
    
    # References
    evidence_refs: List[str] = Field(default_factory=list, description="증거 참조")
    storyboard_card_ids: List[str] = Field(default_factory=list, description="관련 스토리보드 카드 ID")


# =============================================================================
# Video Summary Artifact
# =============================================================================

class VideoSummaryArtifact(BaseModel):
    """Video summary artifact for quick overview."""
    artifact_type: str = Field(default=ArtifactType.VIDEO_SUMMARY.value)
    artifact_id: str = Field(..., description="고유 아티팩트 ID")
    title: str = Field(..., description="영상 제목")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Summary
    synopsis: str = Field(..., description="시놉시스")
    key_themes: List[str] = Field(default_factory=list, description="주요 테마")
    target_audience: Optional[str] = Field(None, description="타겟 오디언스")
    
    # Technical
    total_duration_sec: int = Field(0, description="총 길이")
    scene_count: int = Field(0, description="씬 수")
    
    # Style
    visual_style: Optional[str] = Field(None, description="시각적 스타일")
    capsule_id: Optional[str] = Field(None, description="거장 스타일 ID")
    
    # Related artifacts
    storyboard_id: Optional[str] = Field(None, description="관련 스토리보드 ID")
    shot_list_id: Optional[str] = Field(None, description="관련 샷 리스트 ID")


# =============================================================================
# Artifact Union Type
# =============================================================================

ArtifactUnion = Union[
    StoryboardArtifact,
    ShotListArtifact,
    DataTableArtifact,
    SceneCardArtifact,
    VideoSummaryArtifact,
]


# =============================================================================
# Helper functions
# =============================================================================


def _build_storyboard_card(
    card: Dict[str, Any],
    idx: int = 1,
    *,
    use_duration_hint: bool = False,
) -> Optional[StoryboardCard]:
    """Build a StoryboardCard from raw card dict."""
    if not isinstance(card, dict):
        return None
    
    shot_id = card.get("shot_id") or card.get("card_id") or f"shot-{idx:02d}"
    summary = card.get("description") or card.get("summary") or card.get("note")
    fallback = summary or card.get("composition") or card.get("pacing_note") or f"Shot {idx}"
    description = summary or fallback
    composition = card.get("composition") or card.get("note") or card.get("pacing_note") or fallback
    
    if use_duration_hint:
        duration = _duration_hint_to_int(card.get("duration_hint"))
    else:
        duration = card.get("duration_sec", 4)
    
    return StoryboardCard(
        shot_id=shot_id,
        shot_type=card.get("shot_type", "medium"),
        description=description,
        composition=composition,
        duration_sec=duration,
        dominant_color=card.get("dominant_color", "#333333"),
        accent_color=card.get("accent_color", "#555555"),
        note=card.get("note") or card.get("pacing_note"),
        evidence_refs=card.get("evidence_refs", []),
    )


def _duration_hint_to_int(value: Any, default: int = 4) -> int:
    """Parse duration hint string or number to int."""
    if isinstance(value, (int, float)):
        return max(1, int(value))
    if isinstance(value, str):
        matches = re.findall(r"\d+", value)
        if matches:
            try:
                return max(1, int(matches[0]))
            except ValueError:
                return default
    return default


def create_storyboard_from_capsule_output(
    summary: Dict[str, Any],
    artifact_id: str,
    title: str = "Storyboard",
) -> StoryboardArtifact:
    """Create a StoryboardArtifact from capsule execution output."""
    if not isinstance(summary, dict):
        summary = {}
    
    raw_cards = summary.get("storyboard_cards", [])
    normalized_cards = normalize_storyboard_cards(
        raw_cards,
        palette=summary.get("palette"),
        composition_hints=summary.get("composition_hints"),
        sequence_id=summary.get("sequence_id"),
    )

    cards = [
        card for idx, raw in enumerate(normalized_cards, start=1)
        if (card := _build_storyboard_card(raw, idx)) is not None
    ]
    
    resolved_title = summary.get("title") or summary.get("message") or title

    return StoryboardArtifact(
        artifact_id=artifact_id,
        title=resolved_title,
        capsule_id=summary.get("capsule_id"),
        capsule_version=summary.get("version"),
        cards=cards,
    )


def create_shot_list_from_storyboard(
    storyboard: StoryboardArtifact,
    artifact_id: str,
    title: Optional[str] = None,
) -> ShotListArtifact:
    """Convert a StoryboardArtifact to a ShotListArtifact."""
    shots = []
    
    for idx, card in enumerate(storyboard.cards):
        shot_size_map = {
            "wide": "WS",
            "medium": "MS",
            "close-up": "CU",
            "extreme_close_up": "ECU",
        }
        shot_size = shot_size_map.get(card.shot_type, "MS")
        
        shots.append(ShotListItem(
            shot_id=card.shot_id,
            sequence=f"SEQ-{(idx // 3) + 1:02d}",
            scene=f"SC-{(idx // 5) + 1:02d}",
            shot_size=shot_size,
            action=card.description,
            dialogue=card.dialogue,
            duration=f"{card.duration_sec}s",
            notes=card.note,
        ))
    
    return ShotListArtifact(
        artifact_id=artifact_id,
        title=title or f"{storyboard.title} - Shot List",
        project_id=storyboard.artifact_id,
        shots=shots,
    )


def create_storyboard_from_preview(
    preview: List[Dict[str, Any]],
    artifact_id: str,
    title: str = "Storyboard Preview",
    capsule_id: Optional[str] = None,
) -> Optional[StoryboardArtifact]:
    """Create a StoryboardArtifact from a storyboard preview list."""
    if not isinstance(preview, list) or not preview:
        return None

    cards = [
        card for idx, raw in enumerate(preview, start=1)
        if (card := _build_storyboard_card(raw, idx, use_duration_hint=True)) is not None
    ]

    if not cards:
        return None

    return StoryboardArtifact(
        artifact_id=artifact_id,
        title=title,
        capsule_id=capsule_id,
        cards=cards,
    )


def _coerce_table_value(value: Any) -> Any:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item is not None)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True)
    return value


def _infer_claim_type(claim_id: Optional[str]) -> str:
    if not claim_id:
        return "pattern"
    lowered = str(claim_id).lower()
    if "persona" in lowered:
        return "persona"
    if "_var_" in lowered or "variation" in lowered:
        return "constraint"
    if "logic" in lowered:
        return "pattern"
    return "pattern"


# Data table column definitions (centralized to avoid duplication)
_CLAIM_TABLE_COLUMNS = [
    ("claim_id", "Claim ID", "string"),
    ("claim_type", "Claim Type", "string"),
    ("statement", "Statement", "string"),
    ("evidence_count", "Evidence Count", "number"),
    ("evidence_refs", "Evidence Refs", "string"),
    ("source_id", "Source ID", "string"),
    ("source_pack_id", "Source Pack ID", "string"),
    ("cluster_id", "Cluster ID", "string"),
    ("guide_type", "Guide Type", "string"),
    ("output_type", "Output Type", "string"),
    ("output_language", "Output Language", "string"),
    ("capsule_id", "Capsule ID", "string"),
    ("prompt_version", "Prompt Version", "string"),
    ("model_version", "Model Version", "string"),
    ("generated_at", "Generated At", "string"),
    ("token_input", "Token Input", "number"),
    ("token_output", "Token Output", "number"),
    ("token_total", "Token Total", "number"),
]


def _build_claim_row(
    claim: Dict[str, Any],
    idx: int,
    summary: Dict[str, Any],
    token_usage: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Build a single claim row for the data table."""
    if not isinstance(claim, dict):
        return None
    
    claim_id = claim.get("claim_id") or f"claim-{idx:03d}"
    statement = claim.get("statement") or claim.get("claim_text") or ""
    claim_type = claim.get("claim_type") or _infer_claim_type(claim_id)
    
    evidence_refs = claim.get("evidence_refs")
    if isinstance(evidence_refs, str):
        evidence_refs = [evidence_refs]
    elif not isinstance(evidence_refs, list):
        evidence_refs = []
    evidence_refs = [ref for ref in evidence_refs if isinstance(ref, str)]
    
    return {
        "claim_id": str(claim_id),
        "claim_type": str(claim_type),
        "statement": str(statement),
        "evidence_count": len(evidence_refs),
        "evidence_refs": _coerce_table_value(evidence_refs),
        "source_id": summary.get("source_id", ""),
        "source_pack_id": summary.get("source_pack_id", ""),
        "cluster_id": summary.get("cluster_id", ""),
        "guide_type": summary.get("guide_type", ""),
        "output_type": summary.get("output_type", ""),
        "output_language": summary.get("output_language", ""),
        "capsule_id": summary.get("capsule_id", ""),
        "prompt_version": summary.get("prompt_version", ""),
        "model_version": summary.get("model_version", ""),
        "generated_at": summary.get("generated_at", ""),
        "token_input": token_usage.get("input"),
        "token_output": token_usage.get("output"),
        "token_total": token_usage.get("total"),
    }


def create_data_table_from_claims(
    summary: Dict[str, Any],
    artifact_id: str,
    title: str = "Claim Evidence Table",
) -> Optional[DataTableArtifact]:
    """Create a DataTableArtifact from NotebookLM claim output."""
    if not isinstance(summary, dict):
        return None
    
    claims = summary.get("claims")
    if not isinstance(claims, list) or not claims:
        return None

    columns = [
        DataTableColumn(id=col_id, name=col_name, type=col_type)
        for col_id, col_name, col_type in _CLAIM_TABLE_COLUMNS
    ]

    token_usage = summary.get("token_usage", {})
    if not isinstance(token_usage, dict):
        token_usage = {}

    rows = [
        row for idx, claim in enumerate(claims, start=1)
        if (row := _build_claim_row(claim, idx, summary, token_usage)) is not None
    ]

    evidence_refs = summary.get("evidence_refs", [])
    if isinstance(evidence_refs, str):
        evidence_refs = [evidence_refs]
    source_refs = [ref for ref in evidence_refs if isinstance(ref, str)] if isinstance(evidence_refs, list) else []

    return DataTableArtifact(
        artifact_id=artifact_id,
        title=title,
        columns=columns,
        rows=rows,
        source_refs=source_refs,
        capsule_id=summary.get("capsule_id"),
    )
