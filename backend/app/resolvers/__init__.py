"""
Capsule Resolvers Package

Intent → Capsule Resolver 패턴 구현.
각 Dimension Capsule이 Intent를 해석하여 최적 파라미터를 결정합니다.

Usage:
    ```python
    from app.resolvers import get_resolver, resolve_intent_for_dimension
    from app.schemas.creative_intent import CreativeIntent, CreativeMood
    
    # 방법 1: Resolver 직접 사용
    resolver = get_resolver("VEO")
    params = await resolver.resolve_from_intent(intent)
    
    # 방법 2: 레지스트리 헬퍼 사용
    params = await resolve_intent_for_dimension("VEO", intent)
    
    # 방법 3: dimension_adapter 통합
    from app.resolvers.integration import prepare_dimension_params
    inputs, params = await prepare_dimension_params("VEO", inputs, params, intent)
    ```

Architecture:
    Template → Intent(mood, pace, target) → Capsule Resolver → Params → Execution
"""
from app.resolvers.base import (
    BaseCapsuleResolver,
    ResolvedParams,
    create_resolver_class,
)
from app.resolvers.registry import (
    get_resolver,
    get_all_resolvers,
    list_dimensions,
    resolve_intent_for_dimension,
    resolve_intent_for_all,
    register_resolver,
    unregister_resolver,
)

__all__ = [
    # Base Classes
    "BaseCapsuleResolver",
    "ResolvedParams",
    "create_resolver_class",
    
    # Registry API
    "get_resolver",
    "get_all_resolvers",
    "list_dimensions",
    "resolve_intent_for_dimension",
    "resolve_intent_for_all",
    "register_resolver",
    "unregister_resolver",
]

