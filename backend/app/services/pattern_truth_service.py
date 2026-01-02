"""
Pattern Truth Service

DB 연동 패턴 신뢰도 관리 서비스.
베이지안 갱신 결과를 DB에 저장하고 이력을 추적함.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_pattern import (
    PatternEvidence, 
    PatternConfidenceSnapshot, 
    KellyAllocationLog,
    EvidenceType,
)
from app.schemas.director_pack import DNAInvariant
from app.schemas.bayesian_schemas import Evidence, ConfidenceUpdate
from app.services.bayesian_engine import BayesianTruthEngine
from app.services.kelly_allocator import KellyBasedCreditAllocator

logger = logging.getLogger(__name__)


class PatternTruthService:
    """
    패턴 신뢰도 관리 서비스
    
    Features:
    - 베이지안 갱신 + DB 저장
    - 신뢰도 이력 추적
    - Kelly 배분 로깅
    """
    
    def __init__(self):
        self.bayesian = BayesianTruthEngine()
        self.kelly = KellyBasedCreditAllocator()
    
    async def update_confidence_with_db(
        self,
        db: AsyncSession,
        invariant: DNAInvariant,
        evidence: Evidence,
        pack_id: Optional[str] = None,
    ) -> Tuple[DNAInvariant, ConfidenceUpdate]:
        """
        베이지안 갱신 + DB 저장
        
        Args:
            db: DB 세션
            invariant: 갱신할 규칙
            evidence: 증거
            pack_id: 패턴 팩 ID
        
        Returns:
            (갱신된 invariant, 갱신 정보)
        """
        # 1. 베이지안 갱신
        updated_inv, update = self.bayesian.update_confidence(invariant, evidence)
        
        # 2. 증거 저장
        evidence_record = PatternEvidence(
            rule_id=evidence.rule_id,
            pack_id=pack_id,
            evidence_type=EvidenceType(evidence.evidence_type),
            supports_rule=1 if evidence.supports_rule else 0,
            strength=evidence.strength,
            prior_confidence=update.prior,
            posterior_confidence=update.posterior,
            delta=update.delta,
            source_id=evidence.source_id,
            source_description=evidence.source_description,
        )
        db.add(evidence_record)
        
        # 3. 스냅샷 저장
        snapshot = PatternConfidenceSnapshot(
            rule_id=invariant.rule_id,
            pack_id=pack_id,
            confidence=updated_inv.confidence,
            evidence_count=updated_inv.evidence_count,
            prior_strength=updated_inv.prior_strength,
        )
        db.add(snapshot)
        
        await db.commit()
        
        logger.info(
            f"PatternTruth: {invariant.rule_id} updated "
            f"{update.prior:.3f} → {update.posterior:.3f} (saved to DB)"
        )
        
        return updated_inv, update
    
    async def get_confidence_history(
        self,
        db: AsyncSession,
        rule_id: str,
        limit: int = 100,
    ) -> List[PatternConfidenceSnapshot]:
        """규칙의 신뢰도 이력 조회"""
        result = await db.execute(
            select(PatternConfidenceSnapshot)
            .where(PatternConfidenceSnapshot.rule_id == rule_id)
            .order_by(desc(PatternConfidenceSnapshot.snapshot_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_evidence_history(
        self,
        db: AsyncSession,
        rule_id: str,
        limit: int = 100,
    ) -> List[PatternEvidence]:
        """규칙의 증거 이력 조회"""
        result = await db.execute(
            select(PatternEvidence)
            .where(PatternEvidence.rule_id == rule_id)
            .order_by(desc(PatternEvidence.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def log_kelly_allocation(
        self,
        db: AsyncSession,
        user_id: str,
        balance: int,
        success_probability: float,
        reward_ratio: float,
        allocation_result: dict,
    ) -> KellyAllocationLog:
        """Kelly 배분 결과 로깅"""
        log = KellyAllocationLog(
            user_id=user_id,
            balance_at_time=balance,
            success_probability=success_probability,
            reward_ratio=reward_ratio,
            kelly_fraction=allocation_result["kelly_fraction"],
            max_safe_investment=allocation_result["max_safe_investment"],
            recommended_runs=allocation_result["recommended_runs"],
            bankruptcy_probability=allocation_result["bankruptcy_probability"],
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        
        logger.info(
            f"Kelly allocation logged: user={user_id}, "
            f"fraction={allocation_result['kelly_fraction']:.3f}"
        )
        
        return log
    
    async def update_kelly_outcome(
        self,
        db: AsyncSession,
        log_id: str,
        actual_investment: int,
        actual_runs: int,
        outcome: str,
    ) -> Optional[KellyAllocationLog]:
        """Kelly 배분 결과 업데이트"""
        result = await db.execute(
            select(KellyAllocationLog)
            .where(KellyAllocationLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if log:
            log.actual_investment = actual_investment
            log.actual_runs = actual_runs
            log.outcome = outcome
            log.completed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Kelly outcome updated: {log_id} -> {outcome}")
        
        return log
    
    async def get_user_kelly_history(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
    ) -> List[KellyAllocationLog]:
        """사용자의 Kelly 배분 이력 조회"""
        result = await db.execute(
            select(KellyAllocationLog)
            .where(KellyAllocationLog.user_id == user_id)
            .order_by(desc(KellyAllocationLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def calculate_user_success_rate(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> float:
        """
        사용자의 과거 성공률 계산
        
        Kelly 배분의 success_probability 추정에 사용
        """
        result = await db.execute(
            select(KellyAllocationLog)
            .where(
                KellyAllocationLog.user_id == user_id,
                KellyAllocationLog.outcome.isnot(None)
            )
        )
        logs = result.scalars().all()
        
        if not logs:
            return 0.5  # 기본값
        
        successes = sum(1 for log in logs if log.outcome == "success")
        return successes / len(logs)


# 싱글톤 인스턴스
pattern_truth_service = PatternTruthService()
