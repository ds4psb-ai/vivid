"""Multi-RAG Type Definitions (P0 2026).

RAG 소스 레지스트리와 지능형 라우터를 위한 타입 정의.

Reference:
    - RAGRouter Paper: https://arxiv.org/abs/2505.23052
    - LlamaIndex Router: https://docs.llamaindex.ai/en/stable/examples/low_level/router/

Usage:
    from app.rag.multi_rag.types import (
        RAGSourceType,
        RAGSourceSpec,
        RAGSourceBackend,
        RouteDecision,
        MultiRAGResult,
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class RAGSourceType(str, Enum):
    """RAG 소스 유형.

    P0 지원 (5개):
        AUTEUR_DNA: 거장 DNA (NotebookLM) - Tier 0
        DIMENSION_KNOWLEDGE: 차원별 지식 (Qdrant) - Tier 1
        USER_HISTORY: 사용자 작업 히스토리
        TEMPLATE_WORKFLOW: 워크플로우 템플릿
        PROJECT_CONTEXT: 현재 프로젝트 컨텍스트

    P1 확장 예정 (4개):
        INDUSTRY_VERTICAL: 업종별 지식 (광고, 영화, 유튜브)
        TREND_DATA: 2026 트렌드 데이터
        COMPLIANCE: 법적/규정 가이드
        CUSTOM: 사용자 정의
    """
    # P0 Core
    AUTEUR_DNA = "auteur_dna"
    DIMENSION_KNOWLEDGE = "dimension"
    USER_HISTORY = "user_history"
    TEMPLATE_WORKFLOW = "template"
    PROJECT_CONTEXT = "project"

    # P1 Extension
    INDUSTRY_VERTICAL = "industry"
    TREND_DATA = "trend"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class RAGSourceSpec(BaseModel):
    """RAG 소스 명세.

    각 RAG 소스의 메타데이터와 라우팅 정보를 정의합니다.
    런타임에 동적으로 등록/해제 가능합니다.

    Attributes:
        source_id: 고유 소스 ID (예: "notebooklm_bong", "qdrant_4d")
        source_type: RAGSourceType enum 값
        display_name: UI 표시명
        description: 소스 설명
        keywords: 라우팅 키워드 (쿼리 매칭용)
        priority: 우선순위 (1-10, 높을수록 우선)
        latency_ms_avg: 평균 응답 시간 (ms)
        cost_per_query: 쿼리당 비용
        backend_type: 백엔드 타입 ("notebooklm", "qdrant", "postgres", "api")
        connection_config: 백엔드별 연결 설정
        max_results: 최대 결과 수
        requires_auth: 인증 필요 여부
        enabled: 활성화 여부

    Example:
        >>> spec = RAGSourceSpec(
        ...     source_id="notebooklm_bong",
        ...     source_type=RAGSourceType.AUTEUR_DNA,
        ...     display_name="봉준호 DNA",
        ...     description="봉준호 감독의 연출 철학과 기법",
        ...     keywords=["봉준호", "계단", "기생충", "살인의추억"],
        ...     priority=10,
        ...     backend_type="notebooklm",
        ...     connection_config={"notebook_id": "DNA_봉준호"},
        ... )
    """
    model_config = ConfigDict(
        frozen=False,  # Allow mutation for runtime updates
        extra="forbid",
        validate_default=True,
    )

    # Identity
    source_id: str = Field(..., min_length=1, max_length=64)
    source_type: RAGSourceType
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)

    # Routing metadata
    keywords: List[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=1, le=10)
    latency_ms_avg: int = Field(default=500, ge=0)
    cost_per_query: float = Field(default=0.0, ge=0.0)

    # Backend config
    backend_type: str = Field(..., min_length=1, max_length=32)
    connection_config: Dict[str, Any] = Field(default_factory=dict)

    # Constraints
    max_results: int = Field(default=10, ge=1, le=100)
    requires_auth: bool = Field(default=False)
    enabled: bool = Field(default=True)

    # Dimension/Auteur affinity (optional)
    dimensions: List[str] = Field(default_factory=list)
    auteur_keys: List[str] = Field(default_factory=list)


@runtime_checkable
class RAGSourceBackend(Protocol):
    """RAG 소스 백엔드 프로토콜 (Duck Typing).

    모든 RAG 백엔드 구현체가 따라야 하는 인터페이스입니다.
    기존 BaseBackend를 확장하며, Protocol 기반으로 정적 타입 체크를 지원합니다.

    Methods:
        query: 쿼리 실행
        health_check: 헬스 체크

    Example:
        >>> class MyBackend:
        ...     async def query(
        ...         self,
        ...         query: str,
        ...         filters: Optional[Dict[str, Any]] = None,
        ...         limit: int = 10,
        ...     ) -> List[Dict[str, Any]]:
        ...         # Implementation
        ...         ...
        ...
        ...     async def health_check(self) -> bool:
        ...         return True
        ...
        >>> backend = MyBackend()
        >>> isinstance(backend, RAGSourceBackend)
        True
    """

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """쿼리 실행.

        Args:
            query: 검색 쿼리
            filters: 메타데이터 필터 (app_key, user_id, dimension 등)
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트. 각 결과는 다음 필드를 포함:
            - id: 문서 ID
            - content: 문서 내용
            - score: 관련성 점수 (0.0-1.0)
            - metadata: 추가 메타데이터
        """
        ...

    async def health_check(self) -> bool:
        """헬스 체크.

        Returns:
            True if healthy, False otherwise
        """
        ...


@dataclass
class RouteDecision:
    """라우팅 결정 결과.

    IntelligentRAGRouter가 쿼리 분석 후 반환하는 라우팅 결정입니다.

    Attributes:
        selected_sources: 선택된 소스 ID 목록
        reasoning: 선택 이유 (디버깅/로깅용)
        confidence: 선택 신뢰도 (0.0-1.0)
        estimated_latency_ms: 예상 총 레이턴시 (ms)
        routing_strategy: 라우팅 전략 ("rule_based", "llm_assisted", "hybrid")

    Example:
        >>> decision = RouteDecision(
        ...     selected_sources=["notebooklm_bong", "qdrant_4d"],
        ...     reasoning="봉준호 키워드 감지 + 4D 분석 요청",
        ...     confidence=0.92,
        ...     estimated_latency_ms=3500,
        ... )
    """
    selected_sources: List[str]
    reasoning: str
    confidence: float
    estimated_latency_ms: int
    routing_strategy: str = "rule_based"


@dataclass
class MultiRAGDocument:
    """Multi-RAG 검색 결과 문서.

    여러 RAG 소스에서 가져온 문서를 통합 형식으로 표현합니다.

    Attributes:
        doc_id: 문서 고유 ID
        content: 문서 내용
        score: 관련성 점수 (원본 또는 RRF)
        source_id: 원본 소스 ID
        source_type: 원본 소스 타입
        rank: 최종 순위
        metadata: 추가 메타데이터
    """
    doc_id: str
    content: str
    score: float
    source_id: str
    source_type: RAGSourceType
    rank: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiRAGResult:
    """Multi-RAG 최종 결과.

    Multi-RAG Orchestrator가 반환하는 최종 결과입니다.
    기존 HybridRAGResult와 호환성을 유지하면서 확장된 기능을 제공합니다.

    Attributes:
        documents: 검색된 문서 목록 (RRF fusion 후)
        sources_used: 사용된 소스 ID 목록
        routing_decision: 라우팅 결정 정보
        total_retrieved: 총 검색된 문서 수 (fusion 전)
        query_time_ms: 총 쿼리 시간 (ms)
        reranked: 리랭킹 적용 여부
        rerank_model: 리랭킹 모델 이름

    Example:
        >>> result = MultiRAGResult(
        ...     documents=[doc1, doc2, doc3],
        ...     sources_used=["notebooklm_bong", "qdrant_4d"],
        ...     routing_decision=decision,
        ...     total_retrieved=25,
        ...     query_time_ms=2100,
        ... )
    """
    documents: List[MultiRAGDocument]
    sources_used: List[str]
    routing_decision: RouteDecision
    total_retrieved: int = 0
    query_time_ms: int = 0
    reranked: bool = False
    rerank_model: Optional[str] = None

    @property
    def confidence(self) -> float:
        """최고 문서 스코어 기반 신뢰도."""
        if not self.documents:
            return 0.0
        return self.documents[0].score

    @property
    def answer(self) -> str:
        """상위 문서 내용 기반 답변 (HybridRAGResult 호환)."""
        if not self.documents:
            return "검색 결과를 찾을 수 없습니다."
        return "\n\n".join(
            doc.content[:500] for doc in self.documents[:3]
        )


# Type aliases for backward compatibility
QueryContext = Dict[str, Any]
BackendResults = List[Dict[str, Any]]
