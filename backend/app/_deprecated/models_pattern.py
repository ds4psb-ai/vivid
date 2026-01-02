"""
Pattern Evidence DB Models

베이지안 증거 및 패턴 신뢰도 저장을 위한 DB 모델.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class EvidenceType(str, enum.Enum):
    """증거 유형"""
    PRODUCTION_RESULT = "production_result"
    USER_FEEDBACK = "user_feedback"
    METRIC = "metric"
    EXPERT = "expert"


class PatternEvidence(Base):
    """
    패턴 증거 테이블
    
    DNAInvariant의 신뢰도를 갱신하는 증거를 저장
    """
    __tablename__ = "pattern_evidences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 관련 규칙
    rule_id = Column(String(255), nullable=False, index=True)
    pack_id = Column(String(255), nullable=True, index=True)
    
    # 증거 정보
    evidence_type = Column(SQLEnum(EvidenceType), nullable=False)
    supports_rule = Column(Integer, nullable=False)  # 1 = 지지, 0 = 반박
    strength = Column(Float, default=1.0)
    
    # 결과
    prior_confidence = Column(Float, nullable=False)
    posterior_confidence = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    
    # 메타데이터
    source_id = Column(String(255), nullable=True)
    source_description = Column(String(1000), nullable=True)
    meta = Column(JSON, default=dict)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)


class PatternConfidenceSnapshot(Base):
    """
    패턴 신뢰도 스냅샷
    
    시간에 따른 신뢰도 변화 추적
    """
    __tablename__ = "pattern_confidence_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 규칙 정보
    rule_id = Column(String(255), nullable=False, index=True)
    pack_id = Column(String(255), nullable=True, index=True)
    
    # 신뢰도
    confidence = Column(Float, nullable=False)
    evidence_count = Column(Integer, default=0)
    prior_strength = Column(Float, default=1.0)
    
    # 타임스탬프
    snapshot_at = Column(DateTime, default=datetime.utcnow, index=True)


class KellyAllocationLog(Base):
    """
    Kelly 배분 로그
    
    크레딧 배분 결정 기록
    """
    __tablename__ = "kelly_allocation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 사용자 정보
    user_id = Column(String(255), nullable=False, index=True)
    
    # 배분 정보
    balance_at_time = Column(Integer, nullable=False)
    success_probability = Column(Float, nullable=False)
    reward_ratio = Column(Float, default=2.0)
    
    # 결과
    kelly_fraction = Column(Float, nullable=False)
    max_safe_investment = Column(Integer, nullable=False)
    recommended_runs = Column(Integer, nullable=False)
    bankruptcy_probability = Column(Float, nullable=False)
    
    # 실제 사용
    actual_investment = Column(Integer, nullable=True)
    actual_runs = Column(Integer, nullable=True)
    outcome = Column(String(50), nullable=True)  # success, failure, pending
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
