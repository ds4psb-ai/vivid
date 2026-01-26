"""
Capsule Resolver Base Classes and Interfaces

Intent → Capsule Resolver 패턴의 핵심 인터페이스 정의.
각 Dimension Capsule은 이 베이스 클래스를 상속받아 구현합니다.

Design Goals:
- 명시적 인터페이스: resolve_from_intent() 시그니처 표준화
- 확장 가능: RAG 컨텍스트, 캐싱 훅 제공
- 타입 안전: Pydantic 모델 활용
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from dataclasses import dataclass, field
import logging

from app.schemas.creative_intent import CreativeIntent, CreativeMood, CreativePace, TargetAudience

logger = logging.getLogger(__name__)


# =========================================================================
# Result Types
# =========================================================================

@dataclass
class ResolvedParams:
    """Resolver가 반환하는 해석된 파라미터"""
    
    # 캡슐 실행에 필요한 파라미터
    params: Dict[str, Any] = field(default_factory=dict)
    
    # RAG에서 가져온 추가 컨텍스트
    rag_context: Optional[Dict[str, Any]] = None
    
    # 해석 메타데이터
    resolved_from: str = "intent"  # "intent", "fallback"
    confidence: float = 1.0
    
    # 디버그/추적 정보
    resolution_notes: list = field(default_factory=list)
    
    def merge_with(self, other: Dict[str, Any]) -> "ResolvedParams":
        """다른 파라미터와 병합 (other가 우선)"""
        merged_params = {**self.params, **other}
        return ResolvedParams(
            params=merged_params,
            rag_context=self.rag_context,
            resolved_from=self.resolved_from,
            confidence=self.confidence,
            resolution_notes=self.resolution_notes + [f"merged: {list(other.keys())}"]
        )


# =========================================================================
# Base Resolver Interface
# =========================================================================

class BaseCapsuleResolver(ABC):
    """
    모든 Dimension Resolver의 베이스 클래스
    
    각 Dimension은 이 클래스를 상속받아:
    1. INTENT_MAP 정의: mood/pace/target → params 매핑
    2. resolve_from_intent() 구현: Intent + RAG → 최종 파라미터
    3. get_default_params() 구현: 기본값 반환
    
    Example:
        ```python
        class VEOResolver(BaseCapsuleResolver):
            dimension_code = "VEO"
            
            INTENT_MAP = {
                "cinematic": {"lens": "anamorphic", "fps": 24},
                "energetic": {"lens": "wide", "fps": 60},
            }
            
            async def resolve_from_intent(self, intent, rag_context):
                base = self.INTENT_MAP.get(intent.mood.value, {})
                return ResolvedParams(params=base)
        ```
    """
    
    # 서브클래스에서 정의
    dimension_code: str = "UNKNOWN"
    dimension_name: str = "Unknown Dimension"
    
    # Intent → Base Params 매핑 (서브클래스에서 오버라이드)
    INTENT_MAP: Dict[str, Dict[str, Any]] = {}
    
    # Pace별 조정 맵
    PACE_ADJUSTMENTS: Dict[str, Dict[str, Any]] = {
        "fast": {},
        "slow": {},
        "dynamic": {},
        "contemplative": {},
    }
    
    # Target별 조정 맵
    TARGET_ADJUSTMENTS: Dict[str, Dict[str, Any]] = {
        "expert": {},
        "beginner": {},
        "general": {},
        "kids": {},
        "professional": {},
    }
    
    # =========================================================================
    # Abstract Methods - 서브클래스에서 구현 필수
    # =========================================================================
    
    @abstractmethod
    async def resolve_from_intent(
        self,
        intent: CreativeIntent,
        rag_context: Optional[Dict[str, Any]] = None,
    ) -> ResolvedParams:
        """
        Intent를 캡슐 실행 파라미터로 변환
        
        Args:
            intent: 창작 의도 (mood, pace, target 등)
            rag_context: RAG 소스에서 가져온 추가 컨텍스트
            
        Returns:
            ResolvedParams: 해석된 파라미터 + 메타데이터
        """
        pass
    
    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        """
        기본 파라미터 반환
        
        Intent가 없거나 해석 실패 시 사용할 fallback 값
        """
        pass
    
    # =========================================================================
    # Template Methods - 공통 로직
    # =========================================================================
    
    def get_intent_map(self) -> Dict[str, Dict[str, Any]]:
        """현재 Intent 매핑 테이블 반환 (검사용)"""
        return self.INTENT_MAP
    
    def _get_base_params(self, mood: CreativeMood) -> Dict[str, Any]:
        """Mood에 대한 기본 파라미터 가져오기"""
        return self.INTENT_MAP.get(mood.value, self.get_default_params())
    
    def _apply_pace_adjustments(
        self, 
        params: Dict[str, Any], 
        pace: CreativePace
    ) -> Dict[str, Any]:
        """Pace에 따른 조정 적용"""
        adjustments = self.PACE_ADJUSTMENTS.get(pace.value, {})
        return {**params, **adjustments}
    
    def _apply_target_adjustments(
        self,
        params: Dict[str, Any],
        target: TargetAudience
    ) -> Dict[str, Any]:
        """Target Audience에 따른 조정 적용"""
        adjustments = self.TARGET_ADJUSTMENTS.get(target.value, {})
        return {**params, **adjustments}
    
    def _apply_rag_hints(
        self,
        params: Dict[str, Any],
        rag_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """RAG 컨텍스트에서 힌트 적용.
        
        v2: YAML 기반 동적 스타일 힌트 조회.
        거장 레퍼런스, 시각적 스타일, 촬영 기법 등을 파라미터에 반영.
        """
        if not rag_context:
            return params
        
        result = params.copy()
        
        # 1. dimension_code에 해당하는 직접 힌트 적용
        hints_key = f"{self.dimension_code.lower()}_hints"
        hints = rag_context.get(hints_key, {})
        if hints:
            logger.debug(f"Applying RAG hints for {self.dimension_code}: {hints}")
            result.update(hints)
        
        # 2. 거장 레퍼런스에서 스타일 힌트 추출 (v2: YAML 기반 동적 조회)
        # ⚠️ ISOLATION: content 컨텍스트에서만 거장 스타일 적용 (다른 앱 타입으로 누출 방지)
        auteur_ref = rag_context.get("auteur_reference", "")
        apply_auteur_style = rag_context.get("apply_auteur_style", True)  # 명시적 비활성화 가능
        bounded_context = rag_context.get("bounded_context", "content")  # 기본: content
        
        # 격리 조건: content 컨텍스트가 아니거나 명시적으로 비활성화된 경우 스킵
        if auteur_ref and apply_auteur_style and bounded_context == "content":
            # v2: Registry에서 동적으로 스타일 힌트 조회
            from app.rag.rag_presets import get_auteur_style_hints
            
            # 알려진 거장 키 목록 (Registry에서 조회)
            KNOWN_AUTEURS = ["bong", "epoch", "abyss", "wong", "voltage", "park", "azure"]
            
            auteur_ref_lower = auteur_ref.lower()
            for auteur_key in KNOWN_AUTEURS:
                if auteur_key in auteur_ref_lower:
                    # YAML에서 스타일 힌트 가져오기
                    style_hints = get_auteur_style_hints(auteur_key)
                    if style_hints:
                        for k, v in style_hints.items():
                            if k not in result:  # 기존 값 우선
                                result[k] = v
                        logger.debug(f"Applied auteur style from YAML: {auteur_key} -> {list(style_hints.keys())}")
                    break
            
            # 한글 이름 매핑 (YAML keywords 기반으로 확장 가능)
            KOREAN_AUTEUR_MAPPING = {
                "강주노": "bong", "테오 에포크": "epoch", "오리온 어비스": "abyss",
                "렌 벨벳": "wong", "렉스 볼티지": "voltage", "박찬욱": "park", "신카이": "azure",
            }
            for korean_name, auteur_key in KOREAN_AUTEUR_MAPPING.items():
                if korean_name in auteur_ref_lower:
                    style_hints = get_auteur_style_hints(auteur_key)
                    if style_hints:
                        for k, v in style_hints.items():
                            if k not in result:
                                result[k] = v
                        logger.debug(f"Applied auteur style from YAML (Korean): {korean_name} -> {auteur_key}")
                    break
        
        # 3. RAG 신뢰도 기반 가중치 조절
        confidence = rag_context.get("confidence", 0)
        if confidence >= 0.8:
            result["_rag_confidence"] = "high"
        elif confidence >= 0.5:
            result["_rag_confidence"] = "medium"
        
        return result
    
    async def resolve_with_fallback(
        self,
        intent: Optional[CreativeIntent],
        rag_context: Optional[Dict[str, Any]] = None,
    ) -> ResolvedParams:
        """
        Fallback 로직이 포함된 해석
        
        우선순위:
        1. intent가 있으면 resolve_from_intent 호출
        2. intent가 없으면 default_params 사용
        """
        # 1. Intent 기반 해석
        if intent:
            try:
                result = await self.resolve_from_intent(intent, rag_context)
                return result
            except Exception as e:
                logger.warning(f"{self.dimension_code}: Intent resolution failed: {e}")
                # Fallback to default
        
        # 2. Default
        return ResolvedParams(
            params=self.get_default_params(),
            resolved_from="fallback",
            resolution_notes=["No intent provided, using default params"]
        )


# =========================================================================
# Type Helpers
# =========================================================================

T = TypeVar("T", bound=BaseCapsuleResolver)


def create_resolver_class(
    dimension_code: str,
    dimension_name: str,
    intent_map: Dict[str, Dict[str, Any]],
    default_params: Dict[str, Any],
) -> Type[BaseCapsuleResolver]:
    """
    동적 Resolver 클래스 생성 헬퍼
    
    간단한 매핑만 필요한 Dimension용
    """
    class DynamicResolver(BaseCapsuleResolver):
        pass
    
    DynamicResolver.dimension_code = dimension_code
    DynamicResolver.dimension_name = dimension_name
    DynamicResolver.INTENT_MAP = intent_map
    DynamicResolver._default_params = default_params
    
    async def resolve_impl(
        self, 
        intent: CreativeIntent,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> ResolvedParams:
        params = self._get_base_params(intent.mood)
        params = self._apply_pace_adjustments(params, intent.pace)
        params = self._apply_target_adjustments(params, intent.target)
        params = self._apply_rag_hints(params, rag_context)
        
        return ResolvedParams(
            params=params,
            rag_context=rag_context,
            resolved_from="intent",
            resolution_notes=[f"Resolved from mood={intent.mood.value}"]
        )
    
    def get_default_impl(self) -> Dict[str, Any]:
        return self._default_params.copy()
    
    DynamicResolver.resolve_from_intent = resolve_impl
    DynamicResolver.get_default_params = get_default_impl
    
    return DynamicResolver


# =========================================================================
# Exports
# =========================================================================

__all__ = [
    "BaseCapsuleResolver",
    "ResolvedParams",
    "create_resolver_class",
]
