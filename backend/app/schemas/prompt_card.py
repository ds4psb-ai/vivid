"""
Prompt Card Schemas - 7 Card AI Video Prompt Generation

Supports:
- Sora 2 Pro (1초/segment, max 25초, storyboard)
- Veo 3.1 (8초 chunk, max 8초, no storyboard)
- Veo 4 (30초/1분 chunk, future)
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TargetPlatform(str, Enum):
    """AI Video Generation Platform"""

    SORA_2_PRO = "sora_2_pro"
    VEO_3_1 = "veo_3.1"
    VEO_4 = "veo_4"


class ShotType(str, Enum):
    """Shot Type Classification"""

    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    POV = "pov"
    OVERHEAD = "overhead"
    SELFIE = "selfie"
    TWO_SHOT = "two_shot"
    GROUP = "group"


class CameraMovement(str, Enum):
    """Camera Movement Types"""

    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACKING = "tracking"
    HANDHELD = "handheld"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"


class VideoPhase(str, Enum):
    """Video Narrative Phase"""

    HOOK = "hook"
    DEVELOPMENT = "development"
    PAYOFF = "payoff"


# ==================
# 7 Prompt Cards
# ==================


class CameraShotCard(BaseModel):
    """Card 1: Camera & Shot"""

    shot_type: Optional[str] = Field(None, description="샷 타입 (wide, medium, close_up, etc.)")
    movement: Optional[str] = Field(None, description="카메라 움직임")
    composition: Optional[str] = Field(None, description="구도 (rule_of_thirds, centered, etc.)")
    angle: Optional[str] = Field(None, description="카메라 앵글 (eye_level, low_angle, high_angle)")
    lens_type: Optional[str] = Field(None, description="렌즈 타입")


class SubjectEntityCard(BaseModel):
    """Card 2: Subject & Entity"""

    main_subject: Optional[str] = Field(None, description="주요 피사체 설명")
    entity_type: Optional[str] = Field(None, description="엔티티 유형 (person, product, animal, etc.)")
    subject_count: Optional[int] = Field(None, description="피사체 수")
    subject_description: Optional[str] = Field(None, description="피사체 상세 설명")


class ActionMotionCard(BaseModel):
    """Card 3: Action & Motion"""

    action: Optional[str] = Field(None, description="주요 액션/동작")
    timing_beats: Optional[List[str]] = Field(None, description="타이밍 비트 리스트")
    motion_intensity: Optional[str] = Field(None, description="동작 강도 (subtle, moderate, intense)")
    transition_type: Optional[str] = Field(None, description="전환 유형")


class SettingContextCard(BaseModel):
    """Card 4: Setting & Context"""

    location: Optional[str] = Field(None, description="장소/배경")
    time_of_day: Optional[str] = Field(None, description="시간대")
    environment: Optional[str] = Field(None, description="환경 특성")
    overlay_text: Optional[str] = Field(None, description="오버레이 텍스트")
    props: Optional[List[str]] = Field(None, description="소품 리스트")


class LightingStyleCard(BaseModel):
    """Card 5: Lighting & Style"""

    lighting: Optional[str] = Field(None, description="조명 스타일")
    mood: Optional[str] = Field(None, description="분위기/무드")
    color_palette: Optional[List[str]] = Field(None, description="컬러 팔레트")
    visual_style: Optional[str] = Field(None, description="비주얼 스타일")


class AudioPacingCard(BaseModel):
    """Card 6: Audio & Pacing"""

    duration_ms: Optional[int] = Field(None, description="총 길이 (밀리초)")
    pacing: Optional[str] = Field(None, description="페이싱 (fast, medium, slow)")
    kick_intervals: Optional[List[Dict[str, Any]]] = Field(None, description="바이럴 킥 구간")
    audio_style: Optional[str] = Field(None, description="오디오 스타일")
    bpm: Optional[int] = Field(None, description="예상 BPM")


class NegativePromptCard(BaseModel):
    """Card 7: Negative Prompt"""

    do_not: Optional[List[str]] = Field(None, description="하지 말아야 할 것들")
    quality_issues: Optional[List[str]] = Field(None, description="품질 이슈 회피 목록")
    constraints: Optional[List[str]] = Field(None, description="제약 조건")


# ==================
# Combined Cards
# ==================


class PromptCards(BaseModel):
    """All 7 Prompt Cards"""

    camera: CameraShotCard = Field(default_factory=CameraShotCard)
    subject: SubjectEntityCard = Field(default_factory=SubjectEntityCard)
    action: ActionMotionCard = Field(default_factory=ActionMotionCard)
    setting: SettingContextCard = Field(default_factory=SettingContextCard)
    lighting: LightingStyleCard = Field(default_factory=LightingStyleCard)
    audio: AudioPacingCard = Field(default_factory=AudioPacingCard)
    negative: NegativePromptCard = Field(default_factory=NegativePromptCard)


# ==================
# Time Segment
# ==================


class SegmentCameraInfo(BaseModel):
    """Time-specific camera information"""

    shot_type: Optional[str] = Field(None, description="샷 타입")
    movement: Optional[str] = Field(None, description="카메라 움직임")
    angle: Optional[str] = Field(None, description="카메라 앵글")


class SegmentMiseEnScene(BaseModel):
    """Time-specific mise-en-scene information"""

    lighting: Optional[str] = Field(None, description="조명")
    color_palette: Optional[List[str]] = Field(None, description="컬러 팔레트")
    composition: Optional[str] = Field(None, description="구도")


class TimeSegment(BaseModel):
    """Generated Time Segment with Prompt"""

    index: int = Field(..., description="세그먼트 인덱스 (0-based)")
    start_ms: int = Field(..., description="시작 시간 (밀리초)")
    end_ms: int = Field(..., description="종료 시간 (밀리초)")
    phase: VideoPhase = Field(..., description="영상 단계 (hook/development/payoff)")
    prompt: str = Field(..., description="해당 구간 프롬프트")
    kick_title: Optional[str] = Field(None, description="관련 바이럴 킥 제목")
    # Time-specific context fields
    what_to_see: Optional[str] = Field(None, description="해당 시간의 구체적 액션/장면")
    camera_info: Optional[SegmentCameraInfo] = Field(None, description="해당 시간의 카메라 정보")
    mise_en_scene: Optional[SegmentMiseEnScene] = Field(None, description="해당 시간의 미장센 정보")
    audio_cue: Optional[str] = Field(None, description="해당 시간의 오디오 큐")


# ==================
# Platform Prompt
# ==================


class PlatformPrompt(BaseModel):
    """Platform-specific Generated Prompt"""

    platform: TargetPlatform = Field(..., description="타겟 플랫폼")
    segments: List[TimeSegment] = Field(..., description="시간 세그먼트 리스트")
    full_prompt: str = Field(..., description="전체 프롬프트 (복사용)")
    segment_count: int = Field(..., description="세그먼트 수")
    total_duration_ms: int = Field(..., description="총 길이 (밀리초)")


# ==================
# API Response Models
# ==================


class PromptCardsResponse(BaseModel):
    """GET /prompt-cards/{video_id} Response"""

    video_id: str
    cards: PromptCards
    has_vdg: bool = Field(..., description="VDG 분석 데이터 존재 여부")
    duration_ms: Optional[int] = Field(None, description="영상 길이 (밀리초)")
    platform_support: Dict[str, bool] = Field(
        default_factory=lambda: {
            "sora_2_pro": True,
            "veo_3.1": True,
            "veo_4": False,  # Coming soon
        }
    )


class GeneratePromptRequest(BaseModel):
    """POST /prompt-cards/{video_id}/generate Request"""

    platform: TargetPlatform = Field(..., description="타겟 플랫폼")
    cards: Optional[PromptCards] = Field(None, description="커스텀 카드 (없으면 자동 추출)")
    duration_ms: Optional[int] = Field(None, description="커스텀 길이 (밀리초)")


class GeneratedPromptResponse(BaseModel):
    """POST /prompt-cards/{video_id}/generate Response"""

    video_id: str
    platform: TargetPlatform
    result: PlatformPrompt
    cards_used: PromptCards
