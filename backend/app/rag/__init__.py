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
from app.rag.tier0_vertex_rag import (
    VertexRAGService,
    VertexRAGConfig,
    VertexRAGResult,
    get_vertex_rag_service,
    reset_vertex_rag_service,
    query_auteur_dna,
    query_dimension_guide,
    query_hybrid,
    cascaded_query,
    create_deep_podcast,
    CORPUS_REGISTRY,
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
    # ============ Tier 0: Vertex AI RAG (Primary) ============
    "VertexRAGService",
    "VertexRAGConfig",
    "VertexRAGResult",
    "get_vertex_rag_service",
    "reset_vertex_rag_service",
    "query_auteur_dna",
    "query_dimension_guide",
    "query_hybrid",
    "cascaded_query",
    "create_deep_podcast",
    "CORPUS_REGISTRY",

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

    # ============ Tier 0: NotebookLM (Legacy) ============
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
]
