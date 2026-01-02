"""
DirectorPack Database Models

DirectorPack 및 DNAInvariant 신뢰도 저장을 위한 DB 모델.
베이지안 갱신 결과가 DB에 영속화됨.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DirectorPackDB(Base):
    """
    DirectorPack DB 모델
    
    패턴 기반 영상 제작 DNA 설정
    """
    __tablename__ = "director_packs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pack_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    pattern_id: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    
    # VDG 참조
    source_vdg_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Pack 내용 (JSON)
    dna_invariants: Mapped[dict] = mapped_column(JSONB, default=list)
    mutation_slots: Mapped[dict] = mapped_column(JSONB, default=list)
    forbidden_mutations: Mapped[dict] = mapped_column(JSONB, default=list)
    checkpoints: Mapped[dict] = mapped_column(JSONB, default=list)
    policy: Mapped[dict] = mapped_column(JSONB, default=dict)
    runtime_contract: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # 메타
    compiled_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DNAInvariantConfidence(Base):
    """
    DNAInvariant 신뢰도 저장
    
    베이지안 갱신 결과를 별도 테이블에 저장하여
    Pack 로딩 시 최신 신뢰도 적용
    """
    __tablename__ = "dna_invariant_confidences"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 규칙 식별
    pack_id: Mapped[str] = mapped_column(String(255), index=True)
    rule_id: Mapped[str] = mapped_column(String(255), index=True)
    
    # 신뢰도 데이터
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    prior_strength: Mapped[float] = mapped_column(Float, default=1.0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 최근 갱신 정보
    last_evidence_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_delta: Mapped[float] = mapped_column(Float, default=0.0)
    
    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    class Config:
        # Unique constraint on (pack_id, rule_id)
        pass


class DirectorPackUsageLog(Base):
    """
    DirectorPack 사용 로그
    
    어떤 Pack이 얼마나 사용되었는지 추적
    """
    __tablename__ = "director_pack_usage_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    pack_id: Mapped[str] = mapped_column(String(255), index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    capsule_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # 사용 결과
    outcome: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # success, failure
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # 메타
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
