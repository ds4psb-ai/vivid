"""Multi-RAG Router Type Definitions (P0 2026).

여러 RAG 소스를 지능적으로 라우팅하기 위한 타입 정의.

Sources:
    - NotebookLM (Tier0): 거장 DNA
    - Multi-Modal Qdrant (Tier1): 차원별 지식
    - User History: 과거 작업 히스토리
    - Template KB: 워크플로우 템플릿
    - Industry Vertical: 업종별 지식
    - Project Context: 현재 프로젝트
    - Trends: 2026 트렌드
    - Compliance: 법적/규정

References:
    - LlamaIndex RouterQueryEngine
    - LangChain Multi-Source Knowledge Router
    - RAGRouter Paper (arxiv.org/abs/2505.23052)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RAGSourceType(str, Enum):
    """RAG 소스 유형."""

    AUTEUR_DNA = "auteur_dna"  # NotebookLM (Tier0)
    MULTIMODAL_DIMENSION = "multimodal"  # multi_rag/ Qdrant (Tier1)
    USER_HISTORY = "user_history"  # PostgreSQL 사용자 히스토리
    TEMPLATE_WORKFLOW = "template"  # 워크플로우 템플릿
    INDUSTRY_VERTICAL = "industry"  # 업종별 지식
    PROJECT_CONTEXT = "project"  # 현재 프로젝트
    TREND_DATA = "trend"  # 2026 트렌드
    COMPLIANCE = "compliance"  # 법적/규정

    @classmethod
    def all(cls) -> list[RAGSourceType]:
        """모든 소스 타입 반환."""
        return list(cls)


class QueryIntent(str, Enum):
    """쿼리 의도 분류 (라우팅 힌트)."""

    STYLE_REFERENCE = "style_reference"  # 스타일/레퍼런스 관련
    TECHNICAL_HOW = "technical_how"  # 기술적 방법
    CREATIVE_IDEA = "creative_idea"  # 창작 아이디어
    HISTORY_RECALL = "history_recall"  # 과거 작업 참조
    TREND_ANALYSIS = "trend_analysis"  # 트렌드 분석
    COMPLIANCE_CHECK = "compliance_check"  # 규정 확인
    GENERAL = "general"  # 일반 질문


@dataclass
class RAGSourceSpec:
    """RAG 소스 명세."""

    source_id: str
    source_type: RAGSourceType
    display_name: str
    description: str

    # 라우팅 메타데이터
    keywords: list[str] = field(default_factory=list)
    priority: int = 5  # 1-10, 높을수록 우선
    latency_ms_avg: int = 500  # 평균 응답 시간
    cost_per_query: float = 0.0  # 쿼리당 비용

    # 연결 설정
    backend_type: str = ""  # "notebooklm", "qdrant", "postgres", "api"
    connection_config: dict[str, Any] = field(default_factory=dict)

    # 제약 조건
    max_results: int = 10
    requires_auth: bool = False
    enabled: bool = True

    # 지원 Dimension (None이면 모두 지원)
    supported_dimensions: list[str] | None = None


@dataclass
class RAGDocument:
    """RAG 검색 결과 문서."""

    id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence_ref: str = ""  # Vivid evidence_refs 형식

    # 선택적 필드
    source_id: str = ""
    source_type: RAGSourceType | None = None
    modality: str = "text"  # text, image, audio, video


@dataclass
class RouteDecision:
    """라우팅 결정 결과."""

    selected_sources: list[str]  # source_ids
    query_intent: QueryIntent
    sub_queries: dict[str, str] = field(default_factory=dict)  # source_id → 최적화 쿼리
    reasoning: str = ""
    confidence: float = 0.0
    estimated_latency_ms: int = 0


@dataclass
class SourceResult:
    """소스별 쿼리 결과."""

    source_id: str
    source_type: RAGSourceType
    documents: list[RAGDocument] = field(default_factory=list)
    latency_ms: float = 0.0
    success: bool = True
    error: str | None = None


@dataclass
class MultiRAGResult:
    """Multi-RAG 오케스트레이터 최종 결과."""

    documents: list[RAGDocument]  # RRF + Rerank 후
    sources_used: list[str]
    routing_decision: RouteDecision
    total_latency_ms: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)  # Vivid 호환

    def get_top_k(self, k: int = 10) -> list[RAGDocument]:
        """상위 k개 문서 반환."""
        return self.documents[:k]


# =============================================================================
# Presets and Defaults
# =============================================================================

# 거장 키워드 (Auteur DNA 라우팅용)
AUTEUR_KEYWORDS: set[str] = {
    "봉준호",
    "bong",
    "쿠브릭",
    "kubrick",
    "놀란",
    "nolan",
    "타란티노",
    "tarantino",
    "스필버그",
    "spielberg",
    "히치콕",
    "hitchcock",
    "스코세이지",
    "scorsese",
    "거장",
    "auteur",
    "스타일",
    "style",
}

# 히스토리 키워드 (User History 라우팅용)
HISTORY_KEYWORDS: set[str] = {
    "이전에",
    "지난번",
    "예전",
    "히스토리",
    "history",
    "과거",
    "before",
    "작업했던",
    "만들었던",
}

# 트렌드 키워드 (Trend Data 라우팅용)
TREND_KEYWORDS: set[str] = {
    "2026",
    "2025",
    "트렌드",
    "trend",
    "최신",
    "latest",
    "요즘",
    "recent",
    "현재",
    "current",
}

# Dimension별 기본 소스 우선순위
DIMENSION_SOURCE_PRIORITY: dict[str, list[RAGSourceType]] = {
    "1D": [RAGSourceType.AUTEUR_DNA, RAGSourceType.MULTIMODAL_DIMENSION],
    "2D": [RAGSourceType.MULTIMODAL_DIMENSION, RAGSourceType.AUTEUR_DNA],
    "3D": [RAGSourceType.MULTIMODAL_DIMENSION, RAGSourceType.AUTEUR_DNA],
    "4D": [RAGSourceType.MULTIMODAL_DIMENSION, RAGSourceType.AUTEUR_DNA],
    "AD": [RAGSourceType.MULTIMODAL_DIMENSION, RAGSourceType.AUTEUR_DNA],
    "STORY": [RAGSourceType.AUTEUR_DNA, RAGSourceType.TEMPLATE_WORKFLOW],
}


def get_default_sources_for_dimension(dimension: str) -> list[RAGSourceType]:
    """Dimension에 대한 기본 소스 우선순위 반환."""
    return DIMENSION_SOURCE_PRIORITY.get(
        dimension,
        [RAGSourceType.MULTIMODAL_DIMENSION, RAGSourceType.AUTEUR_DNA],
    )
