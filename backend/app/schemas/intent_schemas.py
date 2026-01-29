"""
Intent Schemas for Node Chat Integration

채팅 → VDG 노드 변형을 위한 의도(Intent) 스키마.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid

from app.schemas.base import StrictBaseModel


class IntentType(str, Enum):
    """의도 유형"""
    MODIFY = "modify"          # 노드 속성 수정
    CREATE = "create"          # 노드 생성
    DELETE = "delete"          # 노드 삭제
    CONNECT = "connect"        # 노드 연결
    BATCH_EDIT = "batch_edit"  # 다중 노드 편집
    PREVIEW = "preview"        # 미리보기 요청
    UNDO = "undo"              # 취소


class PropertyCategory(str, Enum):
    """속성 카테고리"""
    MOOD = "mood"              # 분위기
    LIGHTING = "lighting"      # 조명
    CAMERA = "camera"          # 카메라
    COLOR = "color"            # 색감
    TIMING = "timing"          # 타이밍
    AUDIO = "audio"            # 오디오
    NARRATIVE = "narrative"    # 서사
    TECHNICAL = "technical"    # 기술적 속성


class PropertyChange(BaseModel):
    """단일 속성 변경"""
    property_name: str
    category: PropertyCategory
    
    old_value: Optional[Any] = None
    new_value: Any
    
    # 변경 이유
    reason: Optional[str] = None
    
    # 추출 신뢰도 (0-1)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class NodeEditIntent(BaseModel):
    """
    노드 편집 의도
    
    자연어에서 추출된 노드 변형 의도
    """
    intent_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    intent_type: IntentType
    
    # 대상
    target_node_id: Optional[str] = None
    target_node_ids: List[str] = Field(default_factory=list)  # batch edit용
    
    # 변경 사항
    property_changes: List[PropertyChange] = Field(default_factory=list)
    
    # 간단한 변경 (Dict 형태)
    simple_changes: Dict[str, Any] = Field(default_factory=dict)
    
    # 원본 텍스트
    original_text: str
    
    # 평가
    stpf_score: Optional[float] = None
    overall_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # 메타
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_simple_dict(self) -> Dict[str, Any]:
        """간단한 Dict 변환"""
        return {
            **self.simple_changes,
            **{pc.property_name: pc.new_value for pc in self.property_changes}
        }


class IntentParseRequest(StrictBaseModel):
    """의도 파싱 요청 (strict mode for type safety)."""

    user_input: str = Field(..., min_length=1, max_length=1000)

    # 컨텍스트
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    current_properties: Optional[Dict[str, Any]] = None

    # 옵션
    include_stpf_eval: bool = True
    language: str = "ko"


class IntentParseResult(BaseModel):
    """의도 파싱 결과"""
    success: bool
    intent: Optional[NodeEditIntent] = None
    
    # 다중 의도 (복잡한 요청)
    intents: List[NodeEditIntent] = Field(default_factory=list)
    
    # 평가
    stpf_score: Optional[float] = None
    stpf_grade: Optional[str] = None
    kelly_recommendation: Optional[str] = None
    
    # 에러
    error: Optional[str] = None
    
    # 메타
    parse_time_ms: Optional[float] = None


# =========================================================================
# 의도 매핑 규칙
# =========================================================================

class IntentMapping(BaseModel):
    """의도 매핑 규칙"""
    keywords: List[str]
    property_changes: Dict[str, Any]
    category: PropertyCategory
    confidence: float = 0.9


# 한국어 의도 매핑
KOREAN_INTENT_MAPPINGS: List[IntentMapping] = [
    # 분위기
    IntentMapping(
        keywords=["극적", "극적으로", "드라마틱"],
        property_changes={"mood": "dramatic", "contrast": "high"},
        category=PropertyCategory.MOOD,
    ),
    IntentMapping(
        keywords=["밝게", "밝은", "환하게"],
        property_changes={"lighting": 8, "mood": "bright"},
        category=PropertyCategory.LIGHTING,
    ),
    IntentMapping(
        keywords=["어둡게", "어두운", "무거운"],
        property_changes={"lighting": 3, "mood": "dark"},
        category=PropertyCategory.LIGHTING,
    ),
    IntentMapping(
        keywords=["차분", "차분하게", "잔잔"],
        property_changes={"mood": "calm", "pacing": "slow"},
        category=PropertyCategory.MOOD,
    ),
    IntentMapping(
        keywords=["긴장", "긴장감", "서스펜스"],
        property_changes={"mood": "tense", "music_tension": "high"},
        category=PropertyCategory.MOOD,
    ),
    
    # 카메라
    IntentMapping(
        keywords=["줌인", "가까이", "클로즈업"],
        property_changes={"camera_motion": "zoom_in", "shot_type": "close_up"},
        category=PropertyCategory.CAMERA,
    ),
    IntentMapping(
        keywords=["줌아웃", "멀리", "와이드"],
        property_changes={"camera_motion": "zoom_out", "shot_type": "wide"},
        category=PropertyCategory.CAMERA,
    ),
    IntentMapping(
        keywords=["천천히", "느리게", "슬로우"],
        property_changes={"speed": 0.7, "pacing": "slow"},
        category=PropertyCategory.TIMING,
    ),
    IntentMapping(
        keywords=["빠르게", "빠른", "역동적"],
        property_changes={"speed": 1.3, "pacing": "fast"},
        category=PropertyCategory.TIMING,
    ),
    IntentMapping(
        keywords=["패닝", "팬", "따라가"],
        property_changes={"camera_motion": "pan"},
        category=PropertyCategory.CAMERA,
    ),
    IntentMapping(
        keywords=["틸트", "위로", "아래로"],
        property_changes={"camera_motion": "tilt"},
        category=PropertyCategory.CAMERA,
    ),
    
    # 색감
    IntentMapping(
        keywords=["따뜻하게", "따뜻한", "웜톤"],
        property_changes={"color_temp": "warm", "color_grade": "warm"},
        category=PropertyCategory.COLOR,
    ),
    IntentMapping(
        keywords=["차갑게", "차가운", "쿨톤"],
        property_changes={"color_temp": "cool", "color_grade": "cool"},
        category=PropertyCategory.COLOR,
    ),
    IntentMapping(
        keywords=["선명하게", "선명한", "비비드"],
        property_changes={"saturation": "high", "contrast": "high"},
        category=PropertyCategory.COLOR,
    ),
    IntentMapping(
        keywords=["부드럽게", "부드러운", "소프트"],
        property_changes={"saturation": "low", "contrast": "low"},
        category=PropertyCategory.COLOR,
    ),
    
    # 오디오
    IntentMapping(
        keywords=["음악", "BGM", "배경음악"],
        property_changes={"has_music": True},
        category=PropertyCategory.AUDIO,
    ),
    IntentMapping(
        keywords=["조용", "조용하게", "무음"],
        property_changes={"volume": 0.2, "music_volume": 0.1},
        category=PropertyCategory.AUDIO,
    ),
]


# =========================================================================
# 복잡한 의도 패턴
# =========================================================================

class ComplexIntentPattern(BaseModel):
    """복잡한 의도 패턴 (ToT 트리거용)"""
    pattern: str
    requires_tot: bool = True
    description: str


COMPLEX_PATTERNS: List[ComplexIntentPattern] = [
    ComplexIntentPattern(
        pattern="전체.*바꿔",
        requires_tot=True,
        description="전체 스토리보드 변경",
    ),
    ComplexIntentPattern(
        pattern="모든.*장면",
        requires_tot=True,
        description="모든 장면 수정",
    ),
    ComplexIntentPattern(
        pattern="처음부터.*끝까지",
        requires_tot=True,
        description="전체 범위 수정",
    ),
    ComplexIntentPattern(
        pattern="여러.*씬",
        requires_tot=True,
        description="다중 씬 수정",
    ),
]
