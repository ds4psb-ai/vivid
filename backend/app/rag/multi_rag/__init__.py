"""Multi-RAG Router Module (P0 2026).

지능형 다중 RAG 소스 라우팅 및 오케스트레이션.

Components:
    - types: 타입 정의 (RAGSourceType, RAGSourceSpec, etc.)
    - registry: RAG 소스 레지스트리 (동적 등록/해제)
    - router: 지능형 RAG 라우터 (규칙 + LLM 기반)
    - orchestrator: Multi-RAG 오케스트레이터 (병렬 실행 + RRF)
    - backends: RAG 소스 백엔드 구현체

Usage:
    from app.rag.multi_rag import (
        # Types
        RAGSourceType,
        RAGSourceSpec,
        RouteDecision,
        MultiRAGResult,
        # Registry
        get_registry,
        # Router & Orchestrator
        IntelligentRAGRouter,
        MultiRAGOrchestrator,
    )

    # Get global registry
    registry = get_registry()

    # Register a new source
    registry.register(
        RAGSourceSpec(
            source_id="my_source",
            source_type=RAGSourceType.CUSTOM,
            ...
        ),
        my_backend,
    )

    # Query via orchestrator
    orchestrator = MultiRAGOrchestrator(registry)
    result = await orchestrator.query("봉준호 계단 연출", context={"auteur_key": "bong"})
"""
from app.rag.multi_rag.types import (
    RAGSourceType,
    RAGSourceSpec,
    RAGSourceBackend,
    RouteDecision,
    MultiRAGDocument,
    MultiRAGResult,
    QueryContext,
    BackendResults,
)
from app.rag.multi_rag.registry import (
    RAGSourceRegistry,
    get_registry,
    reset_registry,
)
from app.rag.multi_rag.router import (
    IntelligentRAGRouter,
    create_router,
)
from app.rag.multi_rag.orchestrator import (
    MultiRAGOrchestrator,
    create_orchestrator,
)
from app.rag.multi_rag.initializer import (
    initialize_multi_rag,
    initialize_multi_rag_sync,
    get_default_sources,
)

__all__ = [
    # Types
    "RAGSourceType",
    "RAGSourceSpec",
    "RAGSourceBackend",
    "RouteDecision",
    "MultiRAGDocument",
    "MultiRAGResult",
    "QueryContext",
    "BackendResults",
    # Registry
    "RAGSourceRegistry",
    "get_registry",
    "reset_registry",
    # Router
    "IntelligentRAGRouter",
    "create_router",
    # Orchestrator
    "MultiRAGOrchestrator",
    "create_orchestrator",
    # Initialization
    "initialize_multi_rag",
    "initialize_multi_rag_sync",
    "get_default_sources",
]
