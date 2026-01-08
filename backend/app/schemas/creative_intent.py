"""
Creative Intent Schema for Capsule Resolver Pattern

이 모듈은 Intent → Capsule Resolver 아키텍처의 핵심 스키마를 정의합니다.
템플릿은 세부 앱 파라미터 대신 CreativeIntent만 선언하고,
각 Dimension Capsule의 Resolver가 이를 해석하여 최적 파라미터를 결정합니다.

Design Philosophy:
- 최소화된 스키마: 필수 필드만 포함
- Enum 활용: LLM 환각 방지
- 확장 가능: domain_sources로 다양한 RAG 소스 지원
- Pydantic v2 베스트 프랙티스 준수

References:
- LangGraph State Schema Pattern
- Pydantic AI Structured Output
- Intent-Based Architecture (2025-2026)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from enum import Enum
import uuid


# =========================================================================
# Core Enums - LLM 환각 방지를 위한 명시적 값 제한
# =========================================================================

class CreativeMood(str, Enum):
    """창작 분위기 - 전체 파이프라인의 톤앤매너 결정"""
    CINEMATIC = "cinematic"       # 영화적, 서사적, 드라마틱
    ENERGETIC = "energetic"       # 역동적, 활기찬, 빠른
    CALM = "calm"                 # 차분한, 명상적, 평화로운
    DOCUMENTARY = "documentary"   # 다큐멘터리, 객관적, 사실적
    EXPERIMENTAL = "experimental" # 실험적, 아방가르드
    NOSTALGIC = "nostalgic"       # 향수적, 레트로
    DARK = "dark"                 # 어둡고 무거운, 긴장감
    WHIMSICAL = "whimsical"       # 기발한, 판타지적


class CreativePace(str, Enum):
    """창작 페이스 - 리듬과 호흡"""
    FAST = "fast"                 # 빠른 컷, 높은 에너지
    SLOW = "slow"                 # 느린 호흡, 여운
    DYNAMIC = "dynamic"           # 가변적, 빠름과 느림의 교차
    CONTEMPLATIVE = "contemplative"  # 사색적, 멈춤이 있는


class TargetAudience(str, Enum):
    """대상 청중 - 난이도와 스타일 결정"""
    EXPERT = "expert"             # 전문가, 디테일 중시
    BEGINNER = "beginner"         # 초보자, 명확한 설명
    GENERAL = "general"           # 일반 대중
    KIDS = "kids"                 # 어린이, 밝고 명확
    PROFESSIONAL = "professional" # B2B, 비즈니스


class ContentDomain(str, Enum):
    """콘텐츠 도메인 - RAG 소스 힌트"""
    # 거장 페르소나
    AUTEUR_BONG = "bong-joon-ho"
    AUTEUR_TARANTINO = "tarantino"
    AUTEUR_NOLAN = "nolan"
    AUTEUR_VILLENEUVE = "villeneuve"
    AUTEUR_WONG = "wong-kar-wai"
    
    # 장르
    GENRE_THRILLER = "thriller"
    GENRE_DRAMA = "drama"
    GENRE_COMEDY = "comedy"
    GENRE_HORROR = "horror"
    GENRE_SCIFI = "sci-fi"
    GENRE_DOCUMENTARY = "documentary"
    GENRE_ANIMATION = "animation"
    
    # 특수 소스 (집단지성)
    SOURCE_SAJU = "saju"           # 사주/주역
    SOURCE_PAPER = "academic"      # 논문/연구
    SOURCE_BOOK = "book"           # 책/교양
    SOURCE_PHILOSOPHY = "philosophy"  # 동양철학
    
    # 플랫폼
    PLATFORM_YOUTUBE = "youtube"
    PLATFORM_TIKTOK = "tiktok"
    PLATFORM_INSTAGRAM = "instagram"
    PLATFORM_FILM = "film"


class OutputFormat(str, Enum):
    """출력 형식"""
    VIDEO = "video"
    IMAGE = "image"
    STORYBOARD = "storyboard"
    SCRIPT = "script"
    AUDIO = "audio"
    MIXED = "mixed"


# =========================================================================
# Intent Metadata - 컨텍스트 및 추적 정보
# =========================================================================

class IntentMetadata(BaseModel):
    """Intent 메타데이터 - 추적 및 분석용"""
    intent_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 사용자 컨텍스트
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    user_tier: Literal["free", "pro", "enterprise"] = "free"
    
    # 원본 정보
    source_template_id: Optional[str] = None
    original_user_input: Optional[str] = None
    
    # 해석 신뢰도
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intent_id": "abc123def456",
                "user_tier": "pro",
                "confidence_score": 0.95
            }
        }
    )


# =========================================================================
# Aesthetic Hints - 미학적 힌트 (선택적 확장)
# =========================================================================

class AestheticHints(BaseModel):
    """미학적 힌트 - Aesthetic Director 연동용"""
    
    # 색감
    color_palette: Optional[List[str]] = Field(
        default=None,
        description="색상 키워드 (e.g., 'warm_autumn', 'neon_night')"
    )
    color_temperature: Optional[Literal["warm", "cool", "neutral"]] = None
    
    # 조명
    lighting_style: Optional[Literal[
        "high-key", "low-key", "natural", "dramatic", "soft"
    ]] = None
    
    # 구도
    composition_style: Optional[Literal[
        "symmetrical", "rule-of-thirds", "golden-ratio", "dynamic", "minimalist"
    ]] = None
    
    # 시각적 참조
    visual_references: Optional[List[str]] = Field(
        default=None,
        description="참조 작품/감독/스타일 키워드"
    )
    
    # 텍스처
    texture_feel: Optional[Literal[
        "grainy", "smooth", "vintage", "modern", "raw"
    ]] = None


# =========================================================================
# CreativeIntent - 핵심 스키마
# =========================================================================

class CreativeIntent(BaseModel):
    """
    창작 의도 스키마 - Intent → Capsule Resolver 패턴의 핵심
    
    이 스키마는 템플릿이 세부 앱 파라미터 대신 선언하는 고수준 창작 의도입니다.
    각 Dimension Capsule의 Resolver가 이 Intent를 해석하여 최적 파라미터를 결정합니다.
    
    Example:
        ```python
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            pace=CreativePace.SLOW,
            target=TargetAudience.EXPERT,
            domain_sources=[ContentDomain.AUTEUR_BONG],
        )
        ```
    
    Benefits:
        - 템플릿-앱 결합도 감소
        - 집단지성 활용 (domain_sources로 다양한 RAG 소스 연결)
        - 하나의 Intent로 전체 파이프라인 톤앤매너 통일
    """
    
    # === Core Attributes (필수) ===
    mood: CreativeMood = Field(
        ...,
        description="전체 파이프라인의 분위기/톤앤매너"
    )
    
    pace: CreativePace = Field(
        default=CreativePace.DYNAMIC,
        description="창작물의 리듬과 호흡"
    )
    
    target: TargetAudience = Field(
        default=TargetAudience.GENERAL,
        description="대상 청중"
    )
    
    # === Domain Hints (선택) ===
    domain_sources: List[ContentDomain] = Field(
        default_factory=list,
        description="RAG 소스 힌트 - 거장, 장르, 특수 소스 등"
    )
    
    output_format: OutputFormat = Field(
        default=OutputFormat.VIDEO,
        description="최종 출력 형식"
    )
    
    # === Aesthetic Hints (선택) ===
    aesthetic_hints: Optional[AestheticHints] = Field(
        default=None,
        description="미학적 힌트 (색감, 조명, 구도 등)"
    )
    
    # === Descriptive Hints (자유형식) ===
    keywords: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="추가 키워드 (최대 10개)"
    )
    
    custom_notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="자유형식 추가 지시사항"
    )
    
    # === Metadata ===
    metadata: IntentMetadata = Field(default_factory=IntentMetadata)
    
    # === Validators ===
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """키워드 정제 - 소문자화, 공백 제거"""
        return [k.strip().lower() for k in v if k.strip()]
    
    @model_validator(mode='after')
    def validate_consistency(self) -> 'CreativeIntent':
        """Intent 일관성 검증"""
        # 어린이 대상인데 어두운 분위기면 경고
        if self.target == TargetAudience.KIDS and self.mood == CreativeMood.DARK:
            # 자동 보정하거나, 실제로는 경고 로깅
            pass
        return self
    
    # === Utility Methods ===
    def get_primary_domain(self) -> Optional[ContentDomain]:
        """첫 번째 domain_source 반환"""
        return self.domain_sources[0] if self.domain_sources else None
    
    def has_auteur_source(self) -> bool:
        """거장 소스가 있는지 확인"""
        return any(
            d.value.startswith("auteur") or d.value in [
                "bong-joon-ho", "tarantino", "nolan", "villeneuve", "wong-kar-wai"
            ]
            for d in self.domain_sources
        )
    
    def has_special_source(self) -> bool:
        """특수 소스 (사주/논문/책) 있는지 확인"""
        special = {ContentDomain.SOURCE_SAJU, ContentDomain.SOURCE_PAPER, 
                   ContentDomain.SOURCE_BOOK, ContentDomain.SOURCE_PHILOSOPHY}
        return bool(set(self.domain_sources) & special)
    
    def to_resolver_context(self) -> Dict[str, Any]:
        """Resolver에 전달할 컨텍스트 딕셔너리 생성"""
        return {
            "mood": self.mood.value,
            "pace": self.pace.value,
            "target": self.target.value,
            "domain_sources": [d.value for d in self.domain_sources],
            "output_format": self.output_format.value,
            "aesthetic_hints": self.aesthetic_hints.model_dump() if self.aesthetic_hints else None,
            "keywords": self.keywords,
            "custom_notes": self.custom_notes,
        }

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mood": "cinematic",
                "pace": "slow",
                "target": "expert",
                "domain_sources": ["bong-joon-ho", "thriller"],
                "output_format": "video",
                "aesthetic_hints": {
                    "color_temperature": "cool",
                    "lighting_style": "low-key"
                },
                "keywords": ["tension", "social-commentary"]
            }
        }
    )


# =========================================================================
# Template Input Preset Migration Schema
# =========================================================================

class TemplateIntentPreset(BaseModel):
    """
    템플릿의 input_preset 마이그레이션 스키마
    
    기존 하드코딩된 앱 파라미터 대신 Intent만 저장합니다.
    
    AS-IS (기존):
        input_preset = {"veo_model": "veo-2", "veo_aspect_ratio": "21:9"}
    
    TO-BE (신규):
        input_preset = {"intent": {...}, "legacy_params": {...}}
    """
    
    # 신규: Intent 기반
    intent: CreativeIntent
    
    # 하위 호환: 마이그레이션 기간 동안 레거시 파라미터 유지
    legacy_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="마이그레이션 기간 동안의 레거시 파라미터 (점진적 deprecated)"
    )
    
    # 버전 관리
    schema_version: str = Field(
        default="2.0",
        description="Input preset 스키마 버전"
    )
    
    def get_resolved_params(self, dimension_code: str) -> Dict[str, Any]:
        """
        특정 Dimension에 대한 파라미터 반환
        
        TODO: Phase 2에서 각 Dimension Resolver와 연동
        """
        # 마이그레이션 기간: 레거시 우선
        if self.legacy_params:
            return self.legacy_params
        
        # Intent 기반 해석 (Phase 2에서 구현)
        return self.intent.to_resolver_context()


# =========================================================================
# Intent Factory - 편의 함수
# =========================================================================

class IntentFactory:
    """CreativeIntent 생성 편의 클래스"""
    
    @staticmethod
    def cinematic_bong() -> CreativeIntent:
        """봉준호 스타일 시네마틱 프리셋"""
        return CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            pace=CreativePace.DYNAMIC,
            target=TargetAudience.EXPERT,
            domain_sources=[
                ContentDomain.AUTEUR_BONG,
                ContentDomain.GENRE_THRILLER,
            ],
            aesthetic_hints=AestheticHints(
                lighting_style="low-key",
                composition_style="symmetrical",
            ),
            keywords=["social-commentary", "tension", "class-divide"]
        )
    
    @staticmethod
    def documentary_calm() -> CreativeIntent:
        """차분한 다큐멘터리 프리셋"""
        return CreativeIntent(
            mood=CreativeMood.DOCUMENTARY,
            pace=CreativePace.CONTEMPLATIVE,
            target=TargetAudience.GENERAL,
            domain_sources=[ContentDomain.GENRE_DOCUMENTARY],
            aesthetic_hints=AestheticHints(
                lighting_style="natural",
                color_temperature="neutral",
            ),
        )
    
    @staticmethod
    def shortform_energetic() -> CreativeIntent:
        """숏폼 바이럴 프리셋"""
        return CreativeIntent(
            mood=CreativeMood.ENERGETIC,
            pace=CreativePace.FAST,
            target=TargetAudience.GENERAL,
            domain_sources=[ContentDomain.PLATFORM_TIKTOK],
            output_format=OutputFormat.VIDEO,
            aesthetic_hints=AestheticHints(
                color_palette=["vibrant", "neon"],
            ),
            keywords=["viral", "hook", "trending"]
        )
    
    @staticmethod
    def saju_guided() -> CreativeIntent:
        """사주 기반 창작 가이드 프리셋"""
        return CreativeIntent(
            mood=CreativeMood.NOSTALGIC,
            pace=CreativePace.CONTEMPLATIVE,
            target=TargetAudience.GENERAL,
            domain_sources=[
                ContentDomain.SOURCE_SAJU,
                ContentDomain.SOURCE_PHILOSOPHY,
            ],
            keywords=["harmony", "natural-flow", "seasonal"]
        )


# =========================================================================
# Exports
# =========================================================================

__all__ = [
    # Core Models
    "CreativeIntent",
    "CreativeMood",
    "CreativePace",
    "TargetAudience",
    "ContentDomain",
    "OutputFormat",
    
    # Supporting Models
    "AestheticHints",
    "IntentMetadata",
    "TemplateIntentPreset",
    
    # Factory
    "IntentFactory",
]
