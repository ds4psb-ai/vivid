"""IP Evidence Models (IP-First Coordination).

IP 워크플로우의 Evidence 추적 모델.

SSoT Decision (SSoT-DEC-002):
- 테이블명: ip_evidence_logs, ip_evidence_chains
- 기존 evidence_logs (humancloud) 충돌 방지

Tables:
    - ip_evidence_logs: 개별 evidence 항목
    - ip_evidence_chains: evidence 체인 (workflow_trace 구성)

Usage:
    from app.models_ip_evidence import (
        IPEvidenceLog,
        IPEvidenceChain,
        EvidenceSource,
    )
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    String,
    DateTime,
    Integer,
    Float,
    Boolean,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class EvidenceSource(str, Enum):
    """Evidence 소스 타입."""
    RAG_TIER0 = "rag_tier0"          # NotebookLM
    RAG_TIER1 = "rag_tier1"          # Qdrant + BM25
    CAPSULE_RUN = "capsule_run"      # Dimension Capsule 실행 결과
    WORKFLOW_NODE = "workflow_node"  # Workflow 노드 결과
    USER_INPUT = "user_input"        # 사용자 입력
    EXTERNAL_API = "external_api"    # 외부 API 호출


class EvidenceStatus(str, Enum):
    """Evidence 상태."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


# =============================================================================
# Models
# =============================================================================

class IPEvidenceLog(Base):
    """IP Evidence Log - 개별 evidence 항목.

    workflow_trace 구성을 위한 단위 evidence 기록.

    Attributes:
        id: Evidence 고유 ID
        generation_id: IP Generation ID
        execution_id: Workflow Execution ID (있는 경우)
        node_result_id: Workflow Node Result ID (있는 경우)

        source: Evidence 소스 타입
        ref_string: evidence_refs 표준 형식 문자열
        content_hash: 콘텐츠 해시 (중복 방지)

        confidence: 신뢰도 점수 (0.0 ~ 1.0)
        relevance_score: 관련성 점수
        quality_score: 품질 점수

        metadata: 추가 메타데이터 (RAG 파라미터, 모델 버전 등)
        raw_content: 원본 콘텐츠 (선택적)
    """
    __tablename__ = "ip_evidence_logs"
    __table_args__ = (
        Index("ix_ip_evidence_logs_generation_id", "generation_id"),
        Index("ix_ip_evidence_logs_execution_id", "execution_id"),
        Index("ix_ip_evidence_logs_source", "source"),
        Index("ix_ip_evidence_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Relations
    generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ip_generations.id", ondelete="SET NULL"),
        nullable=True,
    )
    execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
    )
    node_result_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_node_results.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Evidence Identity
    source: Mapped[str] = mapped_column(
        String(32),
        default=EvidenceSource.CAPSULE_RUN.value,
    )
    ref_string: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )  # e.g., "db:capsule_runs:uuid" or "rag:tier1:doc_id"
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    # Scores
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Status
    status: Mapped[str] = mapped_column(
        String(32),
        default=EvidenceStatus.PENDING.value,
    )

    # Metadata
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class IPEvidenceChain(Base):
    """IP Evidence Chain - Evidence 체인.

    여러 evidence를 연결하여 workflow_trace를 구성.

    Attributes:
        id: Chain 고유 ID
        generation_id: IP Generation ID
        execution_id: Workflow Execution ID

        chain_type: 체인 타입 (sequential, parallel, branching)
        evidence_ids: 포함된 Evidence ID 목록 (순서 보존)

        summary: AI 생성 체인 요약
        total_confidence: 전체 신뢰도 점수
        verified: 검증 완료 여부
    """
    __tablename__ = "ip_evidence_chains"
    __table_args__ = (
        Index("ix_ip_evidence_chains_generation_id", "generation_id"),
        Index("ix_ip_evidence_chains_execution_id", "execution_id"),
        Index("ix_ip_evidence_chains_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Relations
    generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ip_generations.id", ondelete="SET NULL"),
        nullable=True,
    )
    execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Chain Structure
    chain_type: Mapped[str] = mapped_column(
        String(32),
        default="sequential",
    )  # sequential, parallel, branching
    evidence_ids: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )  # List of evidence UUIDs (ordered)

    # Summary
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Verification
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# =============================================================================
# Helper Functions
# =============================================================================

def build_evidence_ref(
    source: EvidenceSource,
    entity_type: str,
    entity_id: str,
    dimension: Optional[str] = None,
) -> str:
    """evidence_refs 표준 형식 문자열 생성.

    Format: "{source}:{entity_type}:{dimension}:{entity_id}"
    or: "{source}:{entity_type}:{entity_id}" (dimension 없는 경우)

    Examples:
        - "db:capsule_runs:uuid-1234"
        - "rag:tier1:4D:doc-5678"
        - "workflow:node_results:uuid-9012"

    Args:
        source: Evidence 소스 타입
        entity_type: 엔티티 타입 (capsule_runs, rag_docs 등)
        entity_id: 엔티티 ID
        dimension: Dimension 코드 (선택)

    Returns:
        표준 형식 문자열
    """
    prefix_map = {
        EvidenceSource.RAG_TIER0: "rag",
        EvidenceSource.RAG_TIER1: "rag",
        EvidenceSource.CAPSULE_RUN: "db",
        EvidenceSource.WORKFLOW_NODE: "workflow",
        EvidenceSource.USER_INPUT: "user",
        EvidenceSource.EXTERNAL_API: "api",
    }

    prefix = prefix_map.get(source, "other")

    if dimension:
        return f"{prefix}:{entity_type}:{dimension}:{entity_id}"
    return f"{prefix}:{entity_type}:{entity_id}"


def parse_evidence_ref(ref_string: str) -> dict:
    """evidence_refs 문자열 파싱.

    Args:
        ref_string: 표준 형식 문자열

    Returns:
        파싱된 딕셔너리
    """
    parts = ref_string.split(":")
    result = {
        "prefix": parts[0] if len(parts) > 0 else "",
        "entity_type": parts[1] if len(parts) > 1 else "",
    }

    if len(parts) == 4:
        result["dimension"] = parts[2]
        result["entity_id"] = parts[3]
    elif len(parts) == 3:
        result["entity_id"] = parts[2]

    return result
