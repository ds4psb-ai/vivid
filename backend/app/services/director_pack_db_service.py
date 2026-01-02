"""
DirectorPack DB Service

DirectorPack DB 연동 서비스.
Pack 저장/로드 및 DNAInvariant 신뢰도 관리.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_director_pack import (
    DirectorPackDB,
    DNAInvariantConfidence,
    DirectorPackUsageLog,
)
from app.schemas.director_pack import DirectorPack, DNAInvariant, PackMeta
from app.schemas.bayesian_schemas import ConfidenceUpdate

logger = logging.getLogger(__name__)


class DirectorPackDBService:
    """
    DirectorPack DB 서비스
    
    Features:
    - Pack 저장/로드
    - DNAInvariant 신뢰도 DB 영속화
    - 사용 로그 기록
    """
    
    async def save_pack(
        self,
        db: AsyncSession,
        pack: DirectorPack,
        compiled_by: Optional[str] = None,
    ) -> DirectorPackDB:
        """
        DirectorPack 저장
        
        기존 Pack이 있으면 업데이트, 없으면 생성
        """
        # 기존 Pack 확인
        result = await db.execute(
            select(DirectorPackDB).where(DirectorPackDB.pack_id == pack.meta.pack_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # 업데이트
            existing.pattern_id = pack.meta.pattern_id
            existing.version = pack.meta.version
            existing.source_vdg_id = pack.meta.source_vdg_id
            existing.dna_invariants = [inv.model_dump() for inv in pack.dna_invariants]
            existing.mutation_slots = [slot.model_dump() for slot in pack.mutation_slots]
            existing.forbidden_mutations = [fm.model_dump() for fm in pack.forbidden_mutations]
            existing.checkpoints = [cp.model_dump() for cp in pack.checkpoints]
            existing.policy = pack.policy.model_dump()
            existing.runtime_contract = pack.runtime_contract.model_dump()
            existing.compiled_by = compiled_by
            
            await db.commit()
            await db.refresh(existing)
            
            logger.info(f"DirectorPack updated: {pack.meta.pack_id}")
            return existing
        else:
            # 생성
            db_pack = DirectorPackDB(
                pack_id=pack.meta.pack_id,
                pattern_id=pack.meta.pattern_id,
                version=pack.meta.version,
                source_vdg_id=pack.meta.source_vdg_id,
                dna_invariants=[inv.model_dump() for inv in pack.dna_invariants],
                mutation_slots=[slot.model_dump() for slot in pack.mutation_slots],
                forbidden_mutations=[fm.model_dump() for fm in pack.forbidden_mutations],
                checkpoints=[cp.model_dump() for cp in pack.checkpoints],
                policy=pack.policy.model_dump(),
                runtime_contract=pack.runtime_contract.model_dump(),
                compiled_by=compiled_by,
            )
            db.add(db_pack)
            await db.commit()
            await db.refresh(db_pack)
            
            logger.info(f"DirectorPack created: {pack.meta.pack_id}")
            return db_pack
    
    async def load_pack(
        self,
        db: AsyncSession,
        pack_id: str,
        apply_confidences: bool = True,
    ) -> Optional[DirectorPack]:
        """
        DirectorPack 로드
        
        Args:
            db: DB 세션
            pack_id: Pack ID
            apply_confidences: DB에 저장된 신뢰도 적용 여부
        
        Returns:
            DirectorPack with applied confidences
        """
        result = await db.execute(
            select(DirectorPackDB).where(DirectorPackDB.pack_id == pack_id)
        )
        db_pack = result.scalar_one_or_none()
        
        if not db_pack:
            return None
        
        # DB 데이터를 Pydantic 모델로 변환
        pack = DirectorPack(
            meta=PackMeta(
                pack_id=db_pack.pack_id,
                pattern_id=db_pack.pattern_id,
                version=db_pack.version,
                source_vdg_id=db_pack.source_vdg_id,
                compiled_at=db_pack.created_at.isoformat(),
                compiled_by=db_pack.compiled_by,
                invariant_count=len(db_pack.dna_invariants),
                slot_count=len(db_pack.mutation_slots),
                forbidden_count=len(db_pack.forbidden_mutations),
                checkpoint_count=len(db_pack.checkpoints),
            ),
            dna_invariants=[DNAInvariant(**inv) for inv in db_pack.dna_invariants],
            mutation_slots=db_pack.mutation_slots,
            forbidden_mutations=db_pack.forbidden_mutations,
            checkpoints=db_pack.checkpoints,
            policy=db_pack.policy,
            runtime_contract=db_pack.runtime_contract,
        )
        
        # 신뢰도 적용
        if apply_confidences:
            pack = await self._apply_confidences(db, pack)
        
        return pack
    
    async def list_packs(
        self,
        db: AsyncSession,
        active_only: bool = True,
    ) -> List[Dict]:
        """Pack 목록 조회"""
        query = select(DirectorPackDB)
        if active_only:
            query = query.where(DirectorPackDB.is_active == True)
        
        result = await db.execute(query.order_by(DirectorPackDB.created_at.desc()))
        packs = result.scalars().all()
        
        return [
            {
                "pack_id": p.pack_id,
                "pattern_id": p.pattern_id,
                "version": p.version,
                "invariant_count": len(p.dna_invariants),
                "created_at": p.created_at.isoformat(),
            }
            for p in packs
        ]
    
    async def update_invariant_confidence(
        self,
        db: AsyncSession,
        pack_id: str,
        rule_id: str,
        update: ConfidenceUpdate,
    ) -> DNAInvariantConfidence:
        """
        DNAInvariant 신뢰도 업데이트
        
        베이지안 갱신 결과를 DB에 저장
        """
        # 기존 레코드 확인
        result = await db.execute(
            select(DNAInvariantConfidence).where(
                and_(
                    DNAInvariantConfidence.pack_id == pack_id,
                    DNAInvariantConfidence.rule_id == rule_id
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # 업데이트
            existing.confidence = update.posterior
            existing.evidence_count = update.evidence_count
            existing.last_delta = update.delta
            existing.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # 생성
            new_conf = DNAInvariantConfidence(
                pack_id=pack_id,
                rule_id=rule_id,
                confidence=update.posterior,
                evidence_count=update.evidence_count,
                last_delta=update.delta,
            )
            db.add(new_conf)
            await db.commit()
            await db.refresh(new_conf)
            
            logger.info(f"Confidence saved: {pack_id}/{rule_id} = {update.posterior:.3f}")
            return new_conf
    
    async def get_invariant_confidences(
        self,
        db: AsyncSession,
        pack_id: str,
    ) -> Dict[str, float]:
        """Pack의 모든 invariant 신뢰도 조회"""
        result = await db.execute(
            select(DNAInvariantConfidence).where(
                DNAInvariantConfidence.pack_id == pack_id
            )
        )
        confidences = result.scalars().all()
        
        return {c.rule_id: c.confidence for c in confidences}
    
    async def _apply_confidences(
        self,
        db: AsyncSession,
        pack: DirectorPack,
    ) -> DirectorPack:
        """DB 신뢰도를 Pack에 적용"""
        confidences = await self.get_invariant_confidences(db, pack.meta.pack_id)
        
        for inv in pack.dna_invariants:
            if inv.rule_id in confidences:
                inv.confidence = confidences[inv.rule_id]
        
        return pack
    
    async def log_usage(
        self,
        db: AsyncSession,
        pack_id: str,
        user_id: str,
        capsule_run_id: Optional[str] = None,
        outcome: Optional[str] = None,
        score: Optional[float] = None,
        meta: Optional[dict] = None,
    ) -> DirectorPackUsageLog:
        """사용 로그 기록"""
        log = DirectorPackUsageLog(
            pack_id=pack_id,
            user_id=user_id,
            capsule_run_id=uuid4() if capsule_run_id else None,
            outcome=outcome,
            score=score,
            meta=meta or {},
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        
        return log
    
    async def get_pack_stats(
        self,
        db: AsyncSession,
        pack_id: str,
    ) -> Dict:
        """Pack 사용 통계"""
        result = await db.execute(
            select(DirectorPackUsageLog).where(
                DirectorPackUsageLog.pack_id == pack_id
            )
        )
        logs = result.scalars().all()
        
        if not logs:
            return {
                "pack_id": pack_id,
                "total_uses": 0,
                "success_rate": 0,
                "avg_score": None,
            }
        
        successes = sum(1 for l in logs if l.outcome == "success")
        scores = [l.score for l in logs if l.score is not None]
        
        return {
            "pack_id": pack_id,
            "total_uses": len(logs),
            "success_rate": successes / len(logs),
            "avg_score": sum(scores) / len(scores) if scores else None,
        }


# 싱글톤 인스턴스
director_pack_db_service = DirectorPackDBService()
