"""RAG Presets for Dimension Apps.

차원별 최적화된 RAG 설정 프리셋.
각 앱이 자동으로 적절한 RAG 전략을 적용하도록 표준화.

Usage:
    from app.rag.rag_presets import get_rag_preset, should_enable_rag
    
    preset = get_rag_preset("AD")  # Aesthetic Director 프리셋
    if should_enable_rag(preset, auteur_key="bong"):
        # RAG 쿼리 실행
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class RAGPreset:
    """RAG 설정 프리셋."""
    # 기본 활성화 설정
    rag_enabled: Union[bool, str] = True  # True, False, "auteur_only"
    auteur_mode: bool = False  # 거장 DNA 우선 모드
    
    # 쿼리 설정
    confidence_threshold: float = 0.5  # 최소 신뢰도
    use_google_search: bool = False  # Google Search Grounding
    dimension_corpus: Optional[str] = None  # 특정 코퍼스 지정
    
    # 캐싱 설정
    cache_ttl: int = 3600  # 초 (기본 1시간)
    cache_enabled: bool = True
    
    # 고급 설정
    max_sources: int = 5  # 최대 소스 수
    answer_max_length: int = 500  # 답변 최대 길이
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rag_enabled": self.rag_enabled,
            "auteur_mode": self.auteur_mode,
            "confidence_threshold": self.confidence_threshold,
            "use_google_search": self.use_google_search,
            "dimension_corpus": self.dimension_corpus,
            "cache_ttl": self.cache_ttl,
            "cache_enabled": self.cache_enabled,
            "max_sources": self.max_sources,
            "answer_max_length": self.answer_max_length,
        }


# =============================================================================
# Dimension → Preset 매핑
# =============================================================================

DIMENSION_RAG_PRESETS: Dict[str, RAGPreset] = {
    # =========================================================================
    # 거장 스타일 차원 - 항상 RAG 활성화
    # =========================================================================
    "AD": RAGPreset(
        rag_enabled=True,
        auteur_mode=True,  # NotebookLM 거장 DNA 우선
        confidence_threshold=0.7,  # 높은 신뢰도 요구
        cache_ttl=7200,  # 2시간 (거장 DNA는 잘 안 바뀜)
        max_sources=5,
        answer_max_length=600,
    ),
    
    # =========================================================================
    # 창작/스토리 차원 - RAG 활성화 + Google Search
    # =========================================================================
    "STORY": RAGPreset(
        rag_enabled=True,
        auteur_mode=False,
        use_google_search=True,  # 트렌드/레퍼런스 검색
        confidence_threshold=0.5,
        dimension_corpus="story_templates",
    ),
    
    "QC": RAGPreset(
        rag_enabled=True,
        auteur_mode=False,
        dimension_corpus="meta_invariants",  # 영화적 진리
        confidence_threshold=0.6,
    ),
    
    # =========================================================================
    # 기본 차원 - 거장 키 있을 때만 RAG
    # =========================================================================
    "1D": RAGPreset(
        rag_enabled="auteur_only",  # 거장 키 있을 때만
        auteur_mode=True,
        confidence_threshold=0.5,
    ),
    
    "2D": RAGPreset(
        rag_enabled="auteur_only",
        auteur_mode=True,
        dimension_corpus="storyboard_templates",
        confidence_threshold=0.5,
    ),
    
    "3D": RAGPreset(
        rag_enabled="auteur_only",
        auteur_mode=True,
        confidence_threshold=0.5,
    ),
    
    "4D": RAGPreset(
        rag_enabled="auteur_only",
        auteur_mode=False,  # 분석은 거장 모드 불필요
        use_google_search=True,  # 영화 정보 검색
        confidence_threshold=0.4,
    ),
    
    # =========================================================================
    # 특수 차원
    # =========================================================================
    "SOUND": RAGPreset(
        rag_enabled=False,  # 사운드는 RAG 불필요
    ),
    
    "VEO": RAGPreset(
        rag_enabled="auteur_only",
        auteur_mode=True,
        confidence_threshold=0.6,
    ),
    
    "AI": RAGPreset(
        rag_enabled=False,  # AI 페르소나는 RAG 불필요
    ),
}

# 기본 프리셋 (정의되지 않은 차원용)
DEFAULT_PRESET = RAGPreset(
    rag_enabled="auteur_only",
    auteur_mode=False,
    confidence_threshold=0.5,
)


# =============================================================================
# Helper Functions
# =============================================================================

def get_rag_preset(dimension_code: str) -> RAGPreset:
    """차원 코드로 RAG 프리셋 조회.
    
    Args:
        dimension_code: 차원 코드 (예: "AD", "1D")
        
    Returns:
        해당 차원의 RAGPreset
    """
    return DIMENSION_RAG_PRESETS.get(dimension_code.upper(), DEFAULT_PRESET)


def should_enable_rag(
    preset: RAGPreset,
    auteur_key: Optional[str] = None,
) -> bool:
    """프리셋과 컨텍스트 기반 RAG 활성화 여부 결정.
    
    Args:
        preset: RAG 프리셋
        auteur_key: 거장 키 (있으면 auteur_only도 활성화)
        
    Returns:
        RAG를 실행해야 하는지 여부
    """
    if preset.rag_enabled is True:
        return True
    elif preset.rag_enabled is False:
        return False
    elif preset.rag_enabled == "auteur_only":
        return auteur_key is not None
    else:
        return False


def get_all_presets() -> Dict[str, Dict[str, Any]]:
    """모든 프리셋을 딕셔너리로 반환 (디버깅/API용)."""
    return {
        code: preset.to_dict()
        for code, preset in DIMENSION_RAG_PRESETS.items()
    }


# =============================================================================
# Template-specific Presets (확장용)
# =============================================================================

TEMPLATE_RAG_OVERRIDES: Dict[str, Dict[str, Any]] = {
    # 템플릿별 프리셋 오버라이드
    "bong-style-drama": {
        "auteur_key": "bong",
        "confidence_threshold": 0.8,
    },
    "nolan-action": {
        "auteur_key": "nolan",
        "use_google_search": True,
    },
    "villeneuve-scifi": {
        "auteur_key": "villeneuve",
        "confidence_threshold": 0.7,
    },
}


def get_template_override(template_id: str) -> Optional[Dict[str, Any]]:
    """템플릿별 RAG 오버라이드 조회."""
    return TEMPLATE_RAG_OVERRIDES.get(template_id)
