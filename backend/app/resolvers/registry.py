"""
Capsule Resolver Registry

모든 Dimension Resolver를 등록하고 dimension_code로 조회할 수 있는 레지스트리.
Workflow Executor가 이 레지스트리를 통해 적절한 Resolver를 가져옵니다.
"""
from __future__ import annotations

from typing import Dict, Optional, Type
import logging

from app.resolvers.base import BaseCapsuleResolver, ResolvedParams
from app.schemas.creative_intent import CreativeIntent

logger = logging.getLogger(__name__)


# =========================================================================
# Resolver Imports - Lazy Loading for Performance
# =========================================================================

_resolvers: Dict[str, BaseCapsuleResolver] = {}
_auto_registered: Dict[str, Type[BaseCapsuleResolver]] = {}
_initialized = False


def resolver_for(*dimension_codes: str):
    """
    Resolver 자동 등록 데코레이터.
    
    Usage:
        @resolver_for("VEO", "VIDEO")  # 여러 코드에 등록 가능
        class VEOResolver(BaseCapsuleResolver):
            ...
    
    이 데코레이터가 적용된 클래스는 registry 초기화 시 자동으로 등록됩니다.
    """
    def decorator(cls: Type[BaseCapsuleResolver]) -> Type[BaseCapsuleResolver]:
        for code in dimension_codes:
            _auto_registered[code.upper()] = cls
            logger.debug(f"Auto-registered resolver {cls.__name__} for {code.upper()}")
        return cls
    return decorator


def _initialize_resolvers():
    """Resolver 인스턴스 초기화 (lazy)"""
    global _resolvers, _initialized
    
    if _initialized:
        return
    
    # 1. Import all resolver modules to trigger @resolver_for decorators
    try:
        from app.resolvers import veo_resolver, sound_resolver, prompt_resolver
    except ImportError as e:
        logger.warning(f"Failed to import some resolvers: {e}")
    
    # 2. Instantiate auto-registered resolvers
    for code, resolver_cls in _auto_registered.items():
        if code not in _resolvers:
            try:
                _resolvers[code] = resolver_cls()
                logger.debug(f"Instantiated resolver for {code}: {resolver_cls.__name__}")
            except Exception as e:
                logger.error(f"Failed to instantiate resolver for {code}: {e}")
    
    # 3. Legacy fallback: direct imports (for backward compatibility)
    if "VEO" not in _resolvers:
        try:
            from app.resolvers.veo_resolver import veo_resolver
            _resolvers["VEO"] = veo_resolver
        except ImportError:
            pass
    
    if "SOUND" not in _resolvers:
        try:
            from app.resolvers.sound_resolver import sound_resolver
            _resolvers["SOUND"] = sound_resolver
        except ImportError:
            pass
    
    if "1D" not in _resolvers:
        try:
            from app.resolvers.prompt_resolver import prompt_resolver
            _resolvers["1D"] = prompt_resolver
        except ImportError:
            pass
    
    _initialized = True
    logger.info(f"Resolver registry initialized with {len(_resolvers)} resolvers: {list(_resolvers.keys())}")


# =========================================================================
# Public API
# =========================================================================

def get_resolver(dimension_code: str) -> Optional[BaseCapsuleResolver]:
    """
    Dimension 코드로 Resolver 가져오기
    
    Args:
        dimension_code: Dimension 식별자 (e.g., "VEO", "1D", "SOUND")
        
    Returns:
        해당 Resolver 인스턴스, 없으면 None
        
    Example:
        ```python
        resolver = get_resolver("VEO")
        if resolver:
            params = await resolver.resolve_from_intent(intent)
        ```
    """
    _initialize_resolvers()
    
    resolver = _resolvers.get(dimension_code.upper())
    if not resolver:
        logger.warning(f"No resolver found for dimension: {dimension_code}")
    
    return resolver


def get_all_resolvers() -> Dict[str, BaseCapsuleResolver]:
    """등록된 모든 Resolver 반환"""
    _initialize_resolvers()
    return _resolvers.copy()


def list_dimensions() -> list[str]:
    """등록된 Dimension 코드 목록"""
    _initialize_resolvers()
    return list(_resolvers.keys())


async def resolve_intent_for_dimension(
    dimension_code: str,
    intent: CreativeIntent,
    rag_context: Optional[Dict] = None,
) -> ResolvedParams:
    """
    Intent를 특정 Dimension의 파라미터로 해석
    
    Args:
        dimension_code: 대상 Dimension
        intent: 창작 의도
        rag_context: RAG에서 가져온 추가 컨텍스트
        
    Returns:
        ResolvedParams: 해석된 파라미터
        
    Raises:
        ValueError: 해당 Dimension에 Resolver가 없는 경우
    """
    resolver = get_resolver(dimension_code)
    
    if not resolver:
        # Fallback: 기본 파라미터 반환
        logger.warning(f"No resolver for {dimension_code}, returning empty params")
        return ResolvedParams(
            params={},
            resolved_from="fallback",
            resolution_notes=[f"No resolver registered for {dimension_code}"]
        )
    
    return await resolver.resolve_from_intent(intent, rag_context)


async def resolve_intent_for_all(
    intent: CreativeIntent,
    rag_context: Optional[Dict] = None,
    dimensions: Optional[list[str]] = None,
) -> Dict[str, ResolvedParams]:
    """
    Intent를 여러 Dimension에 대해 동시에 해석
    
    Args:
        intent: 창작 의도
        rag_context: RAG 컨텍스트
        dimensions: 해석할 Dimension 목록 (None이면 모든 등록된 Dimension)
        
    Returns:
        {dimension_code: ResolvedParams} 매핑
        
    Example:
        ```python
        all_params = await resolve_intent_for_all(intent)
        veo_params = all_params["VEO"].params
        sound_params = all_params["SOUND"].params
        ```
    """
    _initialize_resolvers()
    
    target_dimensions = dimensions or list(_resolvers.keys())
    results = {}
    
    for dim_code in target_dimensions:
        results[dim_code] = await resolve_intent_for_dimension(
            dim_code, intent, rag_context
        )
    
    return results


# =========================================================================
# Registration API (For Dynamic Resolvers)
# =========================================================================

def register_resolver(dimension_code: str, resolver: BaseCapsuleResolver):
    """
    Resolver 동적 등록
    
    테스트나 플러그인 시스템에서 활용
    """
    _initialize_resolvers()
    
    _resolvers[dimension_code.upper()] = resolver
    logger.info(f"Registered resolver for {dimension_code}: {resolver.__class__.__name__}")


def unregister_resolver(dimension_code: str):
    """Resolver 등록 해제"""
    _initialize_resolvers()
    
    if dimension_code.upper() in _resolvers:
        del _resolvers[dimension_code.upper()]
        logger.info(f"Unregistered resolver for {dimension_code}")


# =========================================================================
# Exports
# =========================================================================

__all__ = [
    "get_resolver",
    "get_all_resolvers",
    "list_dimensions",
    "resolve_intent_for_dimension",
    "resolve_intent_for_all",
    "register_resolver",
    "unregister_resolver",
    "resolver_for",  # Auto-register decorator
]
