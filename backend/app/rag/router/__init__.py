"""Multi-RAG Router Module (P0 2026).

여러 RAG 소스를 지능적으로 라우팅하는 시스템.

Components:
    - types: 타입 정의 (RAGSourceSpec, RouteDecision, MultiRAGResult)
    - registry: RAG 소스 레지스트리
    - intelligent_router: 2단계 Hybrid 라우터
    - orchestrator: 병렬 쿼리 및 RRF 융합
    - backends: 소스별 어댑터 (NotebookLM, Qdrant, UserHistory)

Usage:
    # 간편한 쿼리 함수
    from app.rag.router import multi_rag_query

    result = await multi_rag_query(
        query="강주노 감독의 계단 상징",
        dimension="4D",
        auteur_key="bong",
    )

    # 전체 제어
    from app.rag.router import (
        create_orchestrator,
        get_rag_registry,
        IntelligentRAGRouter,
    )

    orchestrator = await create_orchestrator(db_session_factory, llm_client)
    result = await orchestrator.query(query, context)

References:
    - LlamaIndex RouterQueryEngine
    - LangChain Multi-Source Knowledge Router
    - RAGRouter Paper (arxiv.org/abs/2505.23052)
"""

from app.rag.router.types import (
    # Enums
    RAGSourceType,
    QueryIntent,
    # Data Classes
    RAGSourceSpec,
    RAGDocument,
    RouteDecision,
    SourceResult,
    MultiRAGResult,
    # Presets
    AUTEUR_KEYWORDS,
    HISTORY_KEYWORDS,
    TREND_KEYWORDS,
    DIMENSION_SOURCE_PRIORITY,
    get_default_sources_for_dimension,
)
from app.rag.router.registry import (
    RAGSourceRegistry,
    get_rag_registry,
    reset_rag_registry,
    get_default_source_specs,
    setup_default_registry,
)
from app.rag.router.intelligent_router import (
    IntelligentRAGRouter,
    create_intelligent_router,
)
from app.rag.router.orchestrator import (
    MultiRAGOrchestrator,
    create_orchestrator,
    multi_rag_query,
)
from app.rag.router.backends import (
    RAGSourceBackend,
    NotebookLMBackend,
    MultiModalQdrantBackend,
    UserHistoryBackend,
)

__all__ = [
    # Enums
    "RAGSourceType",
    "QueryIntent",
    # Data Classes
    "RAGSourceSpec",
    "RAGDocument",
    "RouteDecision",
    "SourceResult",
    "MultiRAGResult",
    # Registry
    "RAGSourceRegistry",
    "get_rag_registry",
    "reset_rag_registry",
    "get_default_source_specs",
    "setup_default_registry",
    # Router
    "IntelligentRAGRouter",
    "create_intelligent_router",
    # Orchestrator
    "MultiRAGOrchestrator",
    "create_orchestrator",
    "multi_rag_query",
    # Backends
    "RAGSourceBackend",
    "NotebookLMBackend",
    "MultiModalQdrantBackend",
    "UserHistoryBackend",
    # Presets
    "AUTEUR_KEYWORDS",
    "HISTORY_KEYWORDS",
    "TREND_KEYWORDS",
    "DIMENSION_SOURCE_PRIORITY",
    "get_default_sources_for_dimension",
]
