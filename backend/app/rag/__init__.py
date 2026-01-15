"""RAG Pipeline Package for Vivid Dimension Apps.

3-Tier Architecture:
- Tier 0: NotebookLM (범용 지식 베이스) - 읽기 전용, Grounded RAG
- Tier 1: 차원별 Qdrant RAG - 증분 업데이트
- Tier 2: 앱별 컨텍스트 - 메타데이터 필터링

Additional Components:
- LightRAG: 그래프 기반 엔티티/관계 검색 (EMNLP 2025)
- Feedback Loop: Evidence → Qdrant 인덱싱
- Pattern Promoter: 주간/월간 프로모션 스케줄러

Usage:
    from app.rag import get_dimension_rag, get_app_registry

    # 차원별 RAG 검색
    rag = get_dimension_rag("1D")
    results = rag.search("cinematic style guide")

    # 앱별 컨텍스트 검색
    registry = get_app_registry()
    context = registry.get_context_for_app(
        app_key="dimension.aesthetic.direct",
        query="bong joon-ho visual style"
    )

    # NotebookLM Tier 0 검색
    from app.rag import get_notebooklm_service
    service = get_notebooklm_service()
    result = await service.query_notebook("DNA_봉준호", "visual grammar")

    # LightRAG 그래프 검색
    from app.rag import get_lightrag_adapter
    adapter = get_lightrag_adapter()
    result = await adapter.search("봉준호 시각적 특징", search_level="hybrid")
"""
from app.rag.tier1_dimension_rag import (
    Tier1DimensionRAG,
    get_dimension_rag,
    DIMENSION_COLLECTIONS,
)
from app.rag.app_manifest import (
    AppRAGManifest,
    APP_MANIFESTS,
    get_manifest,
    get_dimensions_for_app,
    list_apps_by_dimension,
)
from app.rag.app_registry import (
    AppRAGRegistry,
    get_app_registry,
)
from app.rag.quality_criteria import (
    QualityCriteria,
    QUALITY_WEIGHTS,
    DIMENSION_TECHNICAL_CRITERIA,
    classify_quality_level,
    get_dimension_criteria,
)
from app.rag.quality_evaluator import (
    QualityEvaluator,
    get_quality_evaluator,
    reset_quality_evaluator,
)
from app.rag.feedback_loop import (
    FeedbackLoop,
    FeedbackLoopRAG,
    EvidenceRecord as FeedbackEvidenceRecord,
    get_feedback_loop,
    index_successful_result,
)
from app.rag.tier0_notebooklm import (
    NotebookLMService,
    NotebookLMConfig,
    NotebookQueryResult,
    get_notebooklm_service,
    query_auteur_dna as notebooklm_query_auteur_dna,
    query_dimension_guide as notebooklm_query_dimension_guide,
    NOTEBOOK_REGISTRY,
)
from app.rag.podcast_service import (
    PodcastService,
    PodcastConfig,
    PodcastResult,
    PodcastSource,
    PodcastFormat,
    PodcastLength,
    PodcastStatus,
    get_podcast_service,
    reset_podcast_service,
    generate_deep_dive_podcast,
    generate_debate_podcast,
)
from app.rag.tier2_app_context import (
    AppContextLoader,
    DocumentConfig,
    AppDocument,
    DocumentCollection,
    get_app_context_loader,
)
from app.rag.lightrag_adapter import (
    LightRAGAdapter,
    LightRAGConfig,
    LightRAGSearchResult,
    Entity,
    Relation,
    get_lightrag_adapter,
)
from app.rag.pattern_promoter import (
    PatternPromoter,
    PromotionConfig,
    PromotionCandidate,
    PromotionResult,
    PromotionType,
    get_pattern_promoter,
)
from app.rag.hybrid_rag import (
    HybridRAGResult,
    HybridRAGService,
    hybrid_query,
    get_hybrid_rag_service,
    reset_hybrid_rag_service,
    AUTEUR_KEY_TO_NOTEBOOK,
)
# ============ Phase 4: Observability ============
from app.rag.observability import (
    trace_rag,
    get_langfuse,
    trace_retrieval,
    trace_generation,
)
# ============ Phase 5: Advanced Retrieval ============
from app.rag.graph_rag import (
    graph_query,
    build_auteur_graph,
    get_all_auteurs,
    get_graph_stats,
    GraphRAGResult,
    AuteurGraph,
    Entity as GraphEntity,
    Relationship as GraphRelationship,
)
# P4: Reranker module (Plugin-Registry pattern)
from app.rag.rerankers import (
    BaseReranker,
    RerankResult,
    DocumentToRerank,
    get_reranker,
    list_rerankers,
)
from app.rag.rerankers.vertex import VertexReranker
from app.rag.rerankers.cross_encoder import LocalCrossEncoderReranker
from app.rag.query_expansion import (
    expand_query,
    get_expanded_queries,
)
# ============ Phase 5: Adaptive RAG ============
from app.rag.query_classifier import (
    QueryType,
    QueryClassificationResult,
    RoutingConfig,
    classify_query,
    get_classification_result,
    get_strategy,
    should_skip_retrieval,
)
from app.rag.semantic_router import (
    SemanticRouter,
    get_semantic_router,
    reset_semantic_router,
    reload_routes,
)
from app.rag.strategy_selector import (
    Strategy,
    StrategySelectionResult,
    select_strategy,
    select_strategy_with_details,
    get_strategy_for_query_type,
    list_strategies,
)
from app.rag.direct_llm import (
    DirectLLMResult,
    direct_llm_response,
)

from app.rag.schemas import (
    DimensionType,
    RAGTier,
    RAGDocument,
    RAGSearchRequest,
    RAGSearchResult,
    EvidenceRecord,
    EvidenceIndexRequest,
    EvidenceIndexResponse,
    PromotionBatch,
    NotebookLMSource,
    NotebookLMQuery,
    NotebookLMResponse,
    LightRAGEntity,
    LightRAGRelation,
    LightRAGQueryResult,
    RAGStatsResponse,
    RAGIndexRequest,
    RAGIndexResponse,
    AuteurStyle,
    AuteurMatchRequest,
    AuteurMatchResponse,
    DimensionChainContext,
    WorkflowRAGRequest,
    WorkflowRAGResponse,
)

__all__ = [
    # ============ Podcast Service (Discovery Engine) ============
    "PodcastService",
    "PodcastConfig",
    "PodcastResult",
    "PodcastSource",
    "PodcastFormat",
    "PodcastLength",
    "PodcastStatus",
    "get_podcast_service",
    "reset_podcast_service",
    "generate_deep_dive_podcast",
    "generate_debate_podcast",

    # ============ Tier 0: NotebookLM ============
    "NotebookLMService",
    "NotebookLMConfig",
    "NotebookQueryResult",
    "get_notebooklm_service",
    "notebooklm_query_auteur_dna",
    "notebooklm_query_dimension_guide",
    "NOTEBOOK_REGISTRY",

    # ============ Tier 1: Dimension RAG ============
    "Tier1DimensionRAG",
    "get_dimension_rag",
    "DIMENSION_COLLECTIONS",

    # ============ Tier 2: App Context ============
    "AppContextLoader",
    "DocumentConfig",
    "AppDocument",
    "DocumentCollection",
    "get_app_context_loader",

    # ============ App Manifest ============
    "AppRAGManifest",
    "APP_MANIFESTS",
    "get_manifest",
    "get_dimensions_for_app",
    "list_apps_by_dimension",

    # ============ Registry Service ============
    "AppRAGRegistry",
    "get_app_registry",

    # ============ LightRAG (EMNLP 2025) ============
    "LightRAGAdapter",
    "LightRAGConfig",
    "LightRAGSearchResult",
    "Entity",
    "Relation",
    "get_lightrag_adapter",

    # ============ Quality Framework ============
    "QualityCriteria",
    "QUALITY_WEIGHTS",
    "DIMENSION_TECHNICAL_CRITERIA",
    "classify_quality_level",
    "get_dimension_criteria",
    "QualityEvaluator",
    "get_quality_evaluator",
    "reset_quality_evaluator",

    # ============ Feedback Loop ============
    "FeedbackLoop",
    "FeedbackLoopRAG",
    "FeedbackEvidenceRecord",
    "get_feedback_loop",
    "index_successful_result",

    # ============ Pattern Promoter ============
    "PatternPromoter",
    "PromotionConfig",
    "PromotionCandidate",
    "PromotionResult",
    "PromotionType",
    "get_pattern_promoter",

    # ============ Hybrid RAG ============
    "HybridRAGResult",
    "HybridRAGService",
    "hybrid_query",
    "get_hybrid_rag_service",
    "reset_hybrid_rag_service",
    "AUTEUR_KEY_TO_NOTEBOOK",

    # ============ Schemas ============
    "DimensionType",
    "RAGTier",
    "RAGDocument",
    "RAGSearchRequest",
    "RAGSearchResult",
    "EvidenceRecord",
    "EvidenceIndexRequest",
    "EvidenceIndexResponse",
    "PromotionBatch",
    "NotebookLMSource",
    "NotebookLMQuery",
    "NotebookLMResponse",
    "LightRAGEntity",
    "LightRAGRelation",
    "LightRAGQueryResult",
    "RAGStatsResponse",
    "RAGIndexRequest",
    "RAGIndexResponse",
    "AuteurStyle",
    "AuteurMatchRequest",
    "AuteurMatchResponse",
    "DimensionChainContext",
    "WorkflowRAGRequest",
    "WorkflowRAGResponse",

    # ============ Phase 4: Observability ============
    "trace_rag",
    "get_langfuse",
    "trace_retrieval",
    "trace_generation",

    # ============ Phase 5: Advanced Retrieval ============
    "graph_query",
    "build_auteur_graph",
    "get_all_auteurs",
    "get_graph_stats",
    "GraphRAGResult",
    "AuteurGraph",
    "GraphEntity",
    "GraphRelationship",
    # P4: Rerankers (Plugin-Registry)
    "BaseReranker",
    "VertexReranker",
    "LocalCrossEncoderReranker",
    "RerankResult",
    "DocumentToRerank",
    "get_reranker",
    "list_rerankers",
    "expand_query",
    "get_expanded_queries",
    # ============ Phase 5: Adaptive RAG ============
    "QueryType",
    "QueryClassificationResult",
    "RoutingConfig",
    "classify_query",
    "get_classification_result",
    "get_strategy",
    "should_skip_retrieval",
    "SemanticRouter",
    "get_semantic_router",
    "reset_semantic_router",
    "reload_routes",
    "Strategy",
    "StrategySelectionResult",
    "select_strategy",
    "select_strategy_with_details",
    "get_strategy_for_query_type",
    "list_strategies",
    "DirectLLMResult",
    "direct_llm_response",
]
