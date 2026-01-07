"""RAG Pipeline Pydantic Schemas.

데이터 검증 및 API 요청/응답 스키마.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================

class DimensionType(str, Enum):
    """차원 타입."""
    D1 = "1D"  # Origin - Veo Prompt
    D2 = "2D"  # Blueprint - Storyboard
    D3 = "3D"  # Ambience - Image
    D4 = "4D"  # Moment - Video/Analysis
    AD = "AD"  # Aesthetic Director
    QC = "QC"  # Quality Checker
    AI = "AI"  # Persona Analyzer
    VEO = "VEO"  # Veo Video


class RAGTier(str, Enum):
    """RAG 계층."""
    TIER0 = "tier0"  # NotebookLM (읽기 전용)
    TIER1 = "tier1"  # Dimension Qdrant (증분 업데이트)
    TIER2 = "tier2"  # App Context (메타데이터 필터링)


class PromotionType(str, Enum):
    """패턴 프로모션 타입."""
    WEEKLY = "weekly"   # Tier2 → Tier1
    MONTHLY = "monthly"  # Tier1 → Tier0


class EvidenceStatus(str, Enum):
    """Evidence 상태."""
    PENDING = "pending"
    INDEXED = "indexed"
    PROMOTED = "promoted"
    REJECTED = "rejected"


# ============================================================================
# Base Schemas
# ============================================================================

class RAGDocument(BaseModel):
    """RAG 문서 스키마."""
    doc_id: str = Field(..., description="고유 문서 ID")
    content: str = Field(..., min_length=1, description="문서 내용")
    dimension: DimensionType = Field(..., description="타겟 차원")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    score: float = Field(default=0.0, ge=0, le=1, description="관련도 점수")
    source_tier: RAGTier = Field(default=RAGTier.TIER1, description="소스 계층")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RAGSearchRequest(BaseModel):
    """RAG 검색 요청."""
    query: str = Field(..., min_length=1, max_length=2000, description="검색 쿼리")
    dimensions: List[DimensionType] = Field(default_factory=list, description="타겟 차원들")
    app_key: Optional[str] = Field(None, description="앱 키 필터")
    limit: int = Field(default=5, ge=1, le=50, description="최대 결과 수")
    min_score: float = Field(default=0.5, ge=0, le=1, description="최소 점수")
    include_tiers: List[RAGTier] = Field(
        default_factory=lambda: [RAGTier.TIER1, RAGTier.TIER2],
        description="검색할 계층"
    )
    history_context: Optional[str] = Field(None, description="이력 컨텍스트 (증폭용)")


class RAGSearchResult(BaseModel):
    """RAG 검색 결과."""
    documents: List[RAGDocument] = Field(default_factory=list)
    total_results: int = Field(default=0)
    dimensions_searched: List[str] = Field(default_factory=list)
    tiers_searched: List[str] = Field(default_factory=list)
    query_time_ms: int = Field(default=0)
    formatted_context: str = Field(default="", description="프롬프트 주입용 포맷")


# ============================================================================
# Evidence Schemas
# ============================================================================

class EvidenceRecord(BaseModel):
    """Evidence 레코드 (피드백 루프용)."""
    evidence_id: str = Field(..., description="고유 Evidence ID")
    capsule_id: str = Field(..., description="캡슐 식별자")
    dimension: DimensionType = Field(..., description="타겟 차원")
    content: str = Field(..., description="인덱싱할 콘텐츠")
    inputs_summary: str = Field(default="", description="입력 요약")
    output_summary: str = Field(default="", description="출력 요약")
    quality_score: float = Field(default=0.0, ge=0, le=1, description="품질 점수")
    user_id_hash: str = Field(default="", description="익명화된 사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")
    status: EvidenceStatus = Field(default=EvidenceStatus.PENDING)
    indexed_at: Optional[datetime] = Field(None)
    promoted_at: Optional[datetime] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceIndexRequest(BaseModel):
    """Evidence 인덱싱 요청."""
    capsule_id: str = Field(..., description="캡슐 식별자")
    inputs: Dict[str, Any] = Field(..., description="캡슐 입력")
    output: Dict[str, Any] = Field(..., description="캡슐 출력")
    quality_score: float = Field(default=0.8, ge=0, le=1)
    user_id: Optional[str] = Field(None)
    session_id: Optional[str] = Field(None)


class EvidenceIndexResponse(BaseModel):
    """Evidence 인덱싱 응답."""
    success: bool
    evidence_id: Optional[str] = None
    dimension: Optional[str] = None
    skipped_reason: Optional[str] = None


# ============================================================================
# Pattern Promotion Schemas
# ============================================================================

class PromotionCandidate(BaseModel):
    """프로모션 후보."""
    evidence_id: str
    content: str
    dimension: DimensionType
    quality_score: float
    usage_count: int = Field(default=0, description="사용 횟수")
    success_rate: float = Field(default=0.0, ge=0, le=1, description="성공률")
    created_at: datetime


class PromotionBatch(BaseModel):
    """프로모션 배치."""
    batch_id: str
    promotion_type: PromotionType
    candidates: List[PromotionCandidate]
    status: str = Field(default="pending")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    promoted_count: int = Field(default=0)
    failed_count: int = Field(default=0)


class PromotionResult(BaseModel):
    """프로모션 결과."""
    batch_id: str
    promotion_type: PromotionType
    total_candidates: int
    promoted_count: int
    failed_count: int
    duration_ms: int
    details: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# NotebookLM Schemas (Tier 0)
# ============================================================================

class NotebookLMSource(BaseModel):
    """NotebookLM 소스 문서."""
    source_id: str
    title: str
    content_type: str = Field(default="text")  # text, pdf, url
    content_url: Optional[str] = None
    excerpt: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotebookLMQuery(BaseModel):
    """NotebookLM 쿼리."""
    notebook_id: str = Field(..., description="NotebookLM 노트북 ID")
    query: str = Field(..., min_length=1, max_length=2000)
    max_sources: int = Field(default=5, ge=1, le=20)


class NotebookLMResponse(BaseModel):
    """NotebookLM 응답."""
    answer: str
    sources: List[NotebookLMSource] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    grounding_citations: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# LightRAG Schemas
# ============================================================================

class LightRAGEntity(BaseModel):
    """LightRAG 엔티티."""
    entity_id: str
    name: str
    entity_type: str  # person, concept, technique, style, etc.
    description: str = ""
    attributes: Dict[str, Any] = Field(default_factory=dict)


class LightRAGRelation(BaseModel):
    """LightRAG 관계."""
    relation_id: str
    source_entity: str
    target_entity: str
    relation_type: str  # uses, creates, influences, etc.
    weight: float = Field(default=1.0, ge=0)
    description: str = ""


class LightRAGQueryResult(BaseModel):
    """LightRAG 쿼리 결과."""
    # Low-level: 특정 엔티티 + 관계
    entities: List[LightRAGEntity] = Field(default_factory=list)
    relations: List[LightRAGRelation] = Field(default_factory=list)
    # High-level: 주제/테마
    themes: List[str] = Field(default_factory=list)
    summary: str = ""
    confidence: float = Field(default=0.0)


# ============================================================================
# Admin Schemas
# ============================================================================

class RAGStatsResponse(BaseModel):
    """RAG 통계 응답."""
    total_documents: int = Field(default=0)
    by_dimension: Dict[str, int] = Field(default_factory=dict)
    by_tier: Dict[str, int] = Field(default_factory=dict)
    pending_evidence: int = Field(default=0)
    last_promotion: Optional[datetime] = None
    index_health: str = Field(default="healthy")


class RAGIndexRequest(BaseModel):
    """RAG 문서 인덱싱 요청."""
    documents: List[RAGDocument]
    dimension: DimensionType
    replace_existing: bool = Field(default=False)


class RAGIndexResponse(BaseModel):
    """RAG 문서 인덱싱 응답."""
    success: bool
    indexed_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    errors: List[str] = Field(default_factory=list)


# ============================================================================
# Auteur Style Schemas
# ============================================================================

class AuteurStyle(BaseModel):
    """Auteur 스타일 정의."""
    key: str = Field(..., description="스타일 키 (e.g., 'bong')")
    name: str = Field(..., description="감독 이름")
    name_ko: str = Field(default="", description="한글 이름")
    signature: str = Field(..., description="시그니처 스타일 설명")
    palette_bias: str = Field(default="neutral")  # warm, cool, neutral
    pacing: str = Field(default="medium")  # slow, medium, fast
    camera_style: str = Field(default="controlled")  # static, controlled, dynamic
    techniques: List[str] = Field(default_factory=list)
    avoid_elements: List[str] = Field(default_factory=list)
    reference_films: List[str] = Field(default_factory=list)


class AuteurMatchRequest(BaseModel):
    """Auteur 스타일 매칭 요청."""
    concept: str = Field(..., min_length=1, max_length=2000)
    mood: Optional[str] = None
    reference_style: Optional[str] = None


class AuteurMatchResponse(BaseModel):
    """Auteur 스타일 매칭 응답."""
    matched_auteur: Optional[AuteurStyle] = None
    confidence: float = Field(default=0.0)
    alternative_auteurs: List[AuteurStyle] = Field(default_factory=list)
    style_recommendations: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Workflow Integration Schemas
# ============================================================================

class DimensionChainContext(BaseModel):
    """차원 체이닝 컨텍스트."""
    session_id: str
    current_dimension: DimensionType
    history: List[Dict[str, Any]] = Field(default_factory=list)
    auteur_style: Optional[str] = None
    rag_context: str = Field(default="")
    quality_scores: Dict[str, float] = Field(default_factory=dict)


class WorkflowRAGRequest(BaseModel):
    """워크플로우 RAG 요청."""
    session_id: str
    dimension: DimensionType
    inputs: Dict[str, Any]
    prev_output: Optional[Dict[str, Any]] = None
    auteur_style: Optional[str] = None
    use_rag: bool = Field(default=True)


class WorkflowRAGResponse(BaseModel):
    """워크플로우 RAG 응답."""
    enhanced_inputs: Dict[str, Any]
    rag_context: str
    auteur_context: str = ""
    history_context: str = ""
    sources_used: List[str] = Field(default_factory=list)
