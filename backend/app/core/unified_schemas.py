"""Unified RAG/Workflow Schemas.

LangGraph StateGraph 기반 통합 오케스트레이션 타입 정의.

기존 60+ 타입 → 20개 이하로 통합:
- QueryType (6개) - 쿼리 분류
- Intent (7개) - 사용자 의도
- Dimension (8개) - 차원 코드
- DataType (16개) - I/O 타입

References:
- app/rag/query_classifier.py:QueryType
- app/agents/intent_router.py:Intent, Dimension
- app/workflow/types.py:DataType

Usage:
    from app.core.unified_schemas import (
        QueryType, Intent, Dimension, DataType,
        RetrievedDoc, EvidenceRef, SourceResult,
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums - 통합된 타입 정의
# =============================================================================


class QueryType(str, Enum):
    """쿼리 유형 분류 (P5 통합).

    4개 분류기에서 사용하는 6가지 쿼리 타입.
    """

    SIMPLE_FACTUAL = "simple_factual"
    """일반 사실 쿼리. 전략: direct_llm (검색 생략)."""

    CREATIVE = "creative"
    """창작/생성 쿼리. 전략: minimal_rag (선택적 검색)."""

    DOMAIN_SPECIFIC = "domain_specific"
    """도메인 특화 지식. 전략: ensemble_rrf (NotebookLM + Qdrant)."""

    RECENCY_REQUIRED = "recency_required"
    """최신 정보 필요. 전략: grounding_first (Web Grounding 우선)."""

    MULTI_HOP = "multi_hop"
    """복합 추론/비교. 전략: full_pipeline (전체 파이프라인 + Reranker)."""

    AMBIGUOUS = "ambiguous"
    """분류 불확실. 전략: ensemble_rrf (안전한 기본값)."""


class Intent(str, Enum):
    """사용자 의도 분류 (통합).

    RAG, Agent, Workflow 시스템에서 사용하는 통합 의도.
    """

    GENERATE = "generate"
    """생성 (프롬프트, 이미지, 스토리보드, 사운드, 비디오)."""

    ANALYZE = "analyze"
    """분석 (레퍼런스 해석, 미학 분석, 페르소나 분석)."""

    CREATE = "create"
    """창작 (시나리오, 스토리, 콘텐츠)."""

    VALIDATE = "validate"
    """검증 (퀄리티 체크, 일관성 검사)."""

    WORKFLOW = "workflow"
    """워크플로우 실행 (DAG 기반 멀티스텝)."""

    CHAT = "chat"
    """일반 대화 (RAG/도구 불필요)."""

    UNKNOWN = "unknown"
    """분류 불확실."""


class Dimension(str, Enum):
    """Vivid 4D Framework + Extended Dimensions.

    10+ Dimension 앱에서 사용하는 차원 코드.
    """

    ORIGIN = "1D"      # 프롬프트 생성
    BLUEPRINT = "2D"   # 스토리보드
    AMBIENCE = "3D"    # 이미지/비주얼
    MOMENT = "4D"      # 레퍼런스 분석
    QUALITY = "QC"     # 퀄리티 디렉터
    AESTHETIC = "AD"   # 미학 디렉터
    ABYSS = "AI"       # 심연의 거울 (페르소나)
    VIDEO = "VEO"      # Veo 비디오
    STORY = "STORY"    # 스토리 아키텍트
    SOUND = "SOUND"    # 사운드 크래프터


class DataType(str, Enum):
    """데이터 타입 (I/O 호환성).

    도구 간 데이터 흐름 및 타입 체크용.
    """

    # Basic
    TEXT = "text"
    STRUCTURED_JSON = "structured_json"

    # Media
    IMAGE_URL = "image_url"
    VIDEO_URL = "video_url"
    AUDIO_URL = "audio_url"

    # Creative
    STYLE_HINT = "style_hint"
    STORY_STRUCTURE = "story_structure"
    SCENE_LIST = "scene_list"
    STORYBOARD = "storyboard"
    PROMPT = "prompt"

    # Analysis
    ANALYSIS_RESULT = "analysis_result"
    REFERENCE_DATA = "reference_data"
    COLOR_PALETTE = "color_palette"
    COMPOSITION_GUIDE = "composition_guide"

    # Meta
    USER_CONTEXT = "user_context"
    RAG_CONTEXT = "rag_context"


class CheckpointAction(str, Enum):
    """HITL 체크포인트 액션."""

    APPROVE = "approve"
    """승인: 출력 수락, 계속 진행."""

    REJECT = "reject"
    """거부: 워크플로우 실패 처리."""

    MODIFY = "modify"
    """수정: 수정된 출력으로 진행."""

    SKIP = "skip"
    """건너뛰기: 노드 스킵, 계속 진행."""


class OrchestrationPattern(str, Enum):
    """오케스트레이션 패턴."""

    DIRECT = "direct"
    """직접 실행 (단일 도구)."""

    LINEAR = "linear"
    """순차 실행 (파이프라인)."""

    PARALLEL = "parallel"
    """병렬 실행 (fan-out)."""

    CONDITIONAL = "conditional"
    """조건부 분기."""

    HITL_LOOP = "hitl_loop"
    """HITL 루프 (인간 검토 포함)."""


# =============================================================================
# Data Classes - 통합된 데이터 구조
# =============================================================================


@dataclass(frozen=True)
class RetrievedDoc:
    """검색된 문서.

    RRF 융합 후 최종 문서 형식.
    """

    id: str
    """문서 ID (source:collection:doc_id 형식)."""

    content: str
    """문서 내용."""

    score: float
    """융합 점수 (0.0 ~ 1.0)."""

    source: str
    """소스 (notebooklm, qdrant, vertex, web)."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """추가 메타데이터."""


@dataclass(frozen=True)
class EvidenceRef:
    """Evidence Reference.

    Vivid 규칙: evidence_refs는 List[str] 타입.
    형식: "db:source:ref_id" 또는 "db:collection:dimension:type:id"
    """

    ref: str
    """레퍼런스 문자열."""

    @classmethod
    def from_doc(cls, doc: RetrievedDoc) -> "EvidenceRef":
        """RetrievedDoc에서 EvidenceRef 생성."""
        return cls(ref=f"db:{doc.source}:{doc.id}")

    def __str__(self) -> str:
        return self.ref


@dataclass
class SourceResult:
    """개별 소스 검색 결과.

    MultiRAG 오케스트레이터 + RRF 융합 전 결과.
    """

    source: str
    """소스 이름."""

    docs: List[RetrievedDoc]
    """검색된 문서 목록."""

    latency_ms: float
    """응답 시간 (ms)."""

    error: Optional[str] = None
    """에러 메시지 (실패 시)."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """추가 메타데이터."""


@dataclass
class ClassificationResult:
    """통합 분류 결과.

    4개 분류기 통합 출력.
    """

    query_type: QueryType
    """쿼리 유형."""

    intent: Intent
    """사용자 의도."""

    confidence: float
    """분류 신뢰도 (0.0 ~ 1.0)."""

    dimension: Optional[Dimension] = None
    """연관 차원 (있는 경우)."""

    auteur_key: Optional[str] = None
    """연관 거장 키 (있는 경우)."""

    skip_retrieval: bool = False
    """검색 생략 여부 (simple_factual, creative)."""

    classifier_used: str = "unified"
    """사용된 분류기."""

    latency_ms: float = 0.0
    """분류 소요 시간."""


@dataclass
class RoutingDecision:
    """통합 라우팅 결정.

    5개 라우터 통합 출력.
    """

    selected_sources: List[str]
    """선택된 소스 목록 (notebooklm, qdrant, vertex, web)."""

    selected_tools: List[str]
    """선택된 도구 목록 (도구 ID)."""

    dimension: Optional[Dimension] = None
    """대상 차원."""

    auteur_key: Optional[str] = None
    """대상 거장."""

    strategy: str = "ensemble_rrf"
    """검색 전략."""

    pattern: OrchestrationPattern = OrchestrationPattern.DIRECT
    """오케스트레이션 패턴."""

    sub_queries: List[str] = field(default_factory=list)
    """분해된 서브쿼리 (multi-hop)."""


@dataclass
class RetrievalResult:
    """통합 검색 결과.

    RRF 융합 + Reranker 후 최종 결과.
    """

    docs: List[RetrievedDoc]
    """검색된 문서 목록 (점수순 정렬)."""

    evidence_refs: List[str]
    """Evidence references (Vivid 규칙: List[str])."""

    source_results: Dict[str, SourceResult] = field(default_factory=dict)
    """소스별 원시 결과."""

    total_latency_ms: float = 0.0
    """총 검색 소요 시간."""

    rrf_enabled: bool = True
    """RRF 융합 사용 여부."""

    reranked: bool = False
    """Reranker 적용 여부."""


@dataclass
class ExecutionResult:
    """도구/워크플로우 실행 결과."""

    success: bool
    """성공 여부."""

    output: Any
    """실행 출력."""

    node_id: Optional[str] = None
    """실행된 노드 ID."""

    tool_id: Optional[str] = None
    """실행된 도구 ID."""

    latency_ms: float = 0.0
    """실행 소요 시간."""

    error: Optional[str] = None
    """에러 메시지."""

    hitl_required: bool = False
    """HITL 체크포인트 필요 여부."""


# =============================================================================
# Pydantic Models - API 스키마
# =============================================================================


class UnifiedQueryRequest(BaseModel):
    """통합 쿼리 요청."""

    model_config = ConfigDict(frozen=False, extra="forbid")

    query: str = Field(..., min_length=1, max_length=10000)
    """쿼리 텍스트."""

    user_id: Optional[str] = None
    """사용자 ID (개인화에 사용)."""

    session_id: Optional[str] = None
    """세션 ID (컨텍스트 유지에 사용)."""

    dimension: Optional[str] = None
    """명시적 차원 지정."""

    auteur_key: Optional[str] = None
    """명시적 거장 지정."""

    skip_cache: bool = False
    """캐시 우회 여부."""


class UnifiedQueryResponse(BaseModel):
    """통합 쿼리 응답."""

    model_config = ConfigDict(frozen=False)

    response: str
    """생성된 응답."""

    query_type: str
    """쿼리 유형."""

    intent: str
    """사용자 의도."""

    confidence: float
    """분류 신뢰도."""

    evidence_refs: List[str] = Field(default_factory=list)
    """Evidence references."""

    sources_used: List[str] = Field(default_factory=list)
    """사용된 소스 목록."""

    dimension: Optional[str] = None
    """연관 차원."""

    auteur_key: Optional[str] = None
    """연관 거장."""

    latency_ms: float = 0.0
    """총 소요 시간."""

    cache_hit: bool = False
    """캐시 히트 여부."""


# =============================================================================
# Type Aliases
# =============================================================================


# Condition function type for ConditionalEdge
ConditionFunc = Callable[[Dict[str, Any]], str]

# Router function type
RouterFunc = Callable[[Dict[str, Any]], List[str]]


# =============================================================================
# Strategy Mapping
# =============================================================================


# QueryType → Retrieval Strategy
QUERY_TYPE_STRATEGY_MAP: Dict[QueryType, str] = {
    QueryType.SIMPLE_FACTUAL: "direct_llm",
    QueryType.CREATIVE: "minimal_rag",
    QueryType.DOMAIN_SPECIFIC: "ensemble_rrf",
    QueryType.RECENCY_REQUIRED: "grounding_first",
    QueryType.MULTI_HOP: "full_pipeline",
    QueryType.AMBIGUOUS: "ensemble_rrf",
}

# QueryType → Skip Retrieval
SKIP_RETRIEVAL_TYPES = {QueryType.SIMPLE_FACTUAL, QueryType.CREATIVE}

# Intent → Orchestration Pattern
INTENT_PATTERN_MAP: Dict[Intent, OrchestrationPattern] = {
    Intent.GENERATE: OrchestrationPattern.DIRECT,
    Intent.ANALYZE: OrchestrationPattern.DIRECT,
    Intent.CREATE: OrchestrationPattern.LINEAR,
    Intent.VALIDATE: OrchestrationPattern.DIRECT,
    Intent.WORKFLOW: OrchestrationPattern.CONDITIONAL,
    Intent.CHAT: OrchestrationPattern.DIRECT,
    Intent.UNKNOWN: OrchestrationPattern.DIRECT,
}


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Enums
    "QueryType",
    "Intent",
    "Dimension",
    "DataType",
    "CheckpointAction",
    "OrchestrationPattern",
    # Data Classes
    "RetrievedDoc",
    "EvidenceRef",
    "SourceResult",
    "ClassificationResult",
    "RoutingDecision",
    "RetrievalResult",
    "ExecutionResult",
    # Pydantic Models
    "UnifiedQueryRequest",
    "UnifiedQueryResponse",
    # Type Aliases
    "ConditionFunc",
    "RouterFunc",
    # Mappings
    "QUERY_TYPE_STRATEGY_MAP",
    "SKIP_RETRIEVAL_TYPES",
    "INTENT_PATTERN_MAP",
]
