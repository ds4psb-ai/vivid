"""RAG Presets for Dimension Apps.

차원별 최적화된 RAG 설정 프리셋.
각 앱이 자동으로 적절한 RAG 전략을 적용하도록 표준화.

v2: AppRegistry 통합 - YAML 기반 동적 로딩 지원.

Usage:
    from app.rag.rag_presets import get_rag_preset, should_enable_rag
    
    preset = get_rag_preset("AD")  # Aesthetic Director 프리셋
    if should_enable_rag(preset, auteur_key="bong"):
        # RAG 쿼리 실행
    
    # v2: Registry 기반 거장 조회
    auteur = get_auteur_config("bong")
    if auteur:
        style_hints = auteur.extensions.auteur.style_hints
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# =============================================================================
# v2: Registry Integration (Lazy Loading)
# =============================================================================

_registry_initialized = False

def _ensure_registry():
    """Registry 초기화 (lazy loading)."""
    global _registry_initialized
    if _registry_initialized:
        return
    
    try:
        import sys
        # config 경로 추가
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "apps"
        if config_path.exists():
            sys.path.insert(0, str(config_path.parent))
            from app.core.app_registry import AppRegistry
            AppRegistry.discover(config_path)
            _registry_initialized = True
            logger.info(f"AppRegistry initialized from {config_path}")
    except Exception as e:
        logger.debug(f"Registry initialization skipped: {e}")


def get_auteur_config(auteur_key: str) -> Optional[Any]:
    """v2: Registry에서 거장 설정 조회.
    
    Args:
        auteur_key: 거장 키 (예: "bong", "nolan")
        
    Returns:
        AppConfig or None
    """
    _ensure_registry()
    
    try:
        from app.core.app_registry import AppRegistry
        return AppRegistry.get_by_name(auteur_key)
    except Exception:
        return None


def get_auteur_style_hints(auteur_key: str) -> Dict[str, Any]:
    """v2: 거장의 스타일 힌트 조회.
    
    Args:
        auteur_key: 거장 키
        
    Returns:
        스타일 힌트 딕셔너리
    """
    config = get_auteur_config(auteur_key)
    if config and config.extensions.auteur:
        return config.extensions.auteur.style_hints
    return {}


def get_dimension_config(dimension_code: str) -> Optional[Any]:
    """v2: Registry에서 차원 설정 조회.
    
    Args:
        dimension_code: 차원 코드 (예: "AD", "1D")
        
    Returns:
        AppConfig or None
    """
    _ensure_registry()
    
    try:
        from app.core.app_registry import AppRegistry
        # 대소문자 무관 검색
        return AppRegistry.get_by_name(dimension_code.lower())
    except Exception:
        return None


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
    
    v2: Registry 기반 동적 조회 우선, 하드코딩된 프리셋으로 폴백.
    
    Args:
        dimension_code: 차원 코드 (예: "AD", "1D")
        
    Returns:
        해당 차원의 RAGPreset
    """
    # v2: Registry에서 먼저 조회 시도
    config = get_dimension_config(dimension_code)
    if config and config.has_capability("rag"):
        rag_cap = config.get_capability("rag")
        rag_config = rag_cap.config if rag_cap else {}
        
        # YAML config에서 RAGPreset 생성
        mode = rag_config.get("mode", "auteur_only")
        if mode == "always":
            rag_enabled = True
        elif mode == "disabled" or not rag_cap.enabled:
            rag_enabled = False
        else:
            rag_enabled = "auteur_only"
        
        return RAGPreset(
            rag_enabled=rag_enabled,
            auteur_mode=rag_config.get("auteur_mode", False),
            confidence_threshold=rag_config.get("confidence_threshold", 0.5),
            use_google_search=rag_config.get("use_google_search", False),
            dimension_corpus=rag_config.get("corpus"),
            cache_ttl=rag_config.get("cache_ttl", 3600),
            cache_enabled=True,
            max_sources=rag_config.get("max_sources", 5),
            answer_max_length=rag_config.get("answer_max_length", 500),
        )
    
    # 폴백: 하드코딩된 프리셋
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
