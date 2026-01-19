"""IP Evidence Service - Evidence 기록 및 체인 관리.

IP Generation 및 Workflow 실행의 evidence를 기록합니다.

SSoT Decision (SSoT-DEC-002):
- IPGeneration.evidence_refs (List[str]) → IPEvidenceLog (DB) dual-write
- 기존 evidence_refs 형식은 유지, 새 테이블에도 기록

Usage:
    from app.services.ip_evidence_service import IPEvidenceService

    service = IPEvidenceService(db)
    await service.record_evidence_from_refs(
        generation_id=gen_id,
        execution_id=exec_id,
        evidence_refs=["db:capsule_runs:uuid", "rag:tier1:doc_id"],
    )
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models_ip_evidence import (
    IPEvidenceLog,
    IPEvidenceChain,
    EvidenceSource,
    EvidenceStatus,
    parse_evidence_ref,
)

logger = get_logger("ip_evidence_service")


# Prefix to EvidenceSource mapping
PREFIX_TO_SOURCE = {
    "db": EvidenceSource.CAPSULE_RUN,
    "rag": EvidenceSource.RAG_TIER1,
    "workflow": EvidenceSource.WORKFLOW_NODE,
    "user": EvidenceSource.USER_INPUT,
    "api": EvidenceSource.EXTERNAL_API,
    "capsule": EvidenceSource.CAPSULE_RUN,
    "pattern": EvidenceSource.CAPSULE_RUN,
}


class IPEvidenceService:
    """IP Evidence 기록 서비스.

    evidence_refs 문자열 리스트를 DB 레코드로 변환합니다.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service.

        Args:
            db: 비동기 DB 세션
        """
        self._db = db

    async def record_evidence_from_refs(
        self,
        evidence_refs: List[str],
        generation_id: Optional[uuid.UUID] = None,
        execution_id: Optional[uuid.UUID] = None,
        node_result_id: Optional[uuid.UUID] = None,
        create_chain: bool = True,
    ) -> List[IPEvidenceLog]:
        """evidence_refs 리스트에서 IPEvidenceLog 레코드 생성 (dual-write).

        Args:
            evidence_refs: evidence_refs 문자열 리스트
            generation_id: IP Generation ID
            execution_id: Workflow Execution ID
            node_result_id: Node Result ID
            create_chain: 체인도 함께 생성할지 여부

        Returns:
            생성된 IPEvidenceLog 목록
        """
        if not evidence_refs:
            return []

        logs = []
        evidence_ids = []

        for ref_string in evidence_refs:
            # Parse the ref string
            parsed = parse_evidence_ref(ref_string)
            prefix = parsed.get("prefix", "")

            # Determine source type
            source = PREFIX_TO_SOURCE.get(prefix, EvidenceSource.CAPSULE_RUN)

            # Check for tier0 vs tier1 in RAG
            if prefix == "rag":
                entity_type = parsed.get("entity_type", "")
                if entity_type == "tier0" or "notebooklm" in ref_string.lower():
                    source = EvidenceSource.RAG_TIER0
                else:
                    source = EvidenceSource.RAG_TIER1

            # Create content hash for deduplication
            content_hash = hashlib.sha256(ref_string.encode()).hexdigest()[:32]

            # Check for existing evidence with same hash
            existing = await self._db.execute(
                select(IPEvidenceLog).where(
                    IPEvidenceLog.content_hash == content_hash,
                    IPEvidenceLog.generation_id == generation_id,
                )
            )
            if existing.scalar_one_or_none():
                logger.debug(f"Evidence already exists: {ref_string}")
                continue

            # Create evidence log
            evidence_log = IPEvidenceLog(
                generation_id=generation_id,
                execution_id=execution_id,
                node_result_id=node_result_id,
                source=source.value,
                ref_string=ref_string,
                content_hash=content_hash,
                confidence=0.8,  # Default confidence
                relevance_score=0.0,
                quality_score=0.0,
                status=EvidenceStatus.PENDING.value,
                extra_data=parsed,
            )

            self._db.add(evidence_log)
            await self._db.flush()

            logs.append(evidence_log)
            evidence_ids.append(str(evidence_log.id))

            logger.debug(f"Evidence recorded: {ref_string} → {evidence_log.id}")

        # Create chain if requested
        if create_chain and logs:
            await self.create_evidence_chain(
                generation_id=generation_id,
                execution_id=execution_id,
                evidence_ids=evidence_ids,
                chain_type="sequential",
            )

        logger.info(
            f"[Evidence] Recorded {len(logs)} evidence logs | "
            f"generation={generation_id}"
        )

        return logs

    async def create_evidence_chain(
        self,
        evidence_ids: List[str],
        generation_id: Optional[uuid.UUID] = None,
        execution_id: Optional[uuid.UUID] = None,
        chain_type: str = "sequential",
        summary: Optional[str] = None,
    ) -> IPEvidenceChain:
        """Evidence 체인 생성.

        Args:
            evidence_ids: Evidence ID 목록 (순서 보존)
            generation_id: IP Generation ID
            execution_id: Workflow Execution ID
            chain_type: 체인 타입 (sequential, parallel, branching)
            summary: 체인 요약

        Returns:
            생성된 IPEvidenceChain
        """
        # Calculate total confidence from evidence logs
        total_confidence = 0.0
        if evidence_ids:
            evidence_uuids = [uuid.UUID(eid) for eid in evidence_ids]
            result = await self._db.execute(
                select(IPEvidenceLog).where(
                    IPEvidenceLog.id.in_(evidence_uuids)
                )
            )
            logs = result.scalars().all()
            if logs:
                total_confidence = sum(log.confidence for log in logs) / len(logs)

        chain = IPEvidenceChain(
            generation_id=generation_id,
            execution_id=execution_id,
            chain_type=chain_type,
            evidence_ids=evidence_ids,
            summary=summary,
            total_confidence=total_confidence,
        )

        self._db.add(chain)
        await self._db.flush()

        logger.debug(
            f"Evidence chain created: {chain.id} with {len(evidence_ids)} evidence"
        )

        return chain

    async def get_evidence_for_generation(
        self,
        generation_id: uuid.UUID,
    ) -> List[IPEvidenceLog]:
        """Generation의 모든 evidence 조회.

        Args:
            generation_id: IP Generation ID

        Returns:
            IPEvidenceLog 목록
        """
        result = await self._db.execute(
            select(IPEvidenceLog)
            .where(IPEvidenceLog.generation_id == generation_id)
            .order_by(IPEvidenceLog.created_at)
        )
        return list(result.scalars().all())

    async def get_chain_for_generation(
        self,
        generation_id: uuid.UUID,
    ) -> Optional[IPEvidenceChain]:
        """Generation의 evidence 체인 조회.

        Args:
            generation_id: IP Generation ID

        Returns:
            IPEvidenceChain 또는 None
        """
        result = await self._db.execute(
            select(IPEvidenceChain)
            .where(IPEvidenceChain.generation_id == generation_id)
            .order_by(IPEvidenceChain.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def verify_chain(
        self,
        chain_id: uuid.UUID,
        verified_by: str,
    ) -> IPEvidenceChain:
        """Evidence 체인 검증.

        Args:
            chain_id: Chain ID
            verified_by: 검증자 ID

        Returns:
            업데이트된 IPEvidenceChain
        """
        result = await self._db.execute(
            select(IPEvidenceChain).where(IPEvidenceChain.id == chain_id)
        )
        chain = result.scalar_one_or_none()

        if not chain:
            raise ValueError(f"Chain not found: {chain_id}")

        chain.verified = True
        chain.verified_by = verified_by
        chain.verified_at = datetime.utcnow()

        # Also update all evidence logs to verified
        for evidence_id_str in chain.evidence_ids:
            evidence_id = uuid.UUID(evidence_id_str)
            evidence_result = await self._db.execute(
                select(IPEvidenceLog).where(IPEvidenceLog.id == evidence_id)
            )
            evidence = evidence_result.scalar_one_or_none()
            if evidence:
                evidence.status = EvidenceStatus.VERIFIED.value

        await self._db.flush()

        logger.info(f"Evidence chain verified: {chain_id} by {verified_by}")

        return chain

    def to_workflow_trace(
        self,
        logs: List[IPEvidenceLog],
    ) -> List[Dict[str, Any]]:
        """Evidence logs를 workflow_trace 형식으로 변환.

        Args:
            logs: IPEvidenceLog 목록

        Returns:
            workflow_trace 형식의 딕셔너리 리스트
        """
        return [
            {
                "evidence_id": str(log.id),
                "source": log.source,
                "ref": log.ref_string,
                "confidence": log.confidence,
                "status": log.status,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
