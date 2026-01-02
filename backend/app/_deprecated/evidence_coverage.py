"""Evidence Coverage calculation service.

Calculates coverage metrics for claims backed by evidence.
Coverage formula: claims_with_evidence / total_claims

Reference: 07_EXECUTION_PLAN_2025-12.md Phase 2.3
           32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Claim, ClaimEvidenceMap, EvidenceRef


@dataclass
class CoverageByType:
    """Coverage breakdown by claim type."""
    claim_type: str
    total_claims: int
    claims_with_evidence: int
    coverage_rate: float


@dataclass
class EvidenceCoverageResult:
    """Result of evidence coverage calculation."""
    total_claims: int
    claims_with_evidence: int
    claims_without_evidence: int
    coverage_rate: float
    avg_evidence_per_claim: float
    min_evidence_count: int
    max_evidence_count: int
    coverage_by_type: List[CoverageByType]
    calculated_at: datetime


async def calculate_evidence_coverage(
    session: Optional[AsyncSession] = None,
    *,
    cluster_id: Optional[str] = None,
    min_evidence_count: int = 1,
) -> EvidenceCoverageResult:
    """
    Calculate evidence coverage metrics for all claims.
    
    Args:
        session: Optional DB session (creates one if not provided)
        cluster_id: Optional filter by cluster
        min_evidence_count: Min evidence refs to consider "covered" (default: 1)
    
    Returns:
        EvidenceCoverageResult with coverage metrics
    """
    close_session = session is None
    if session is None:
        session = AsyncSessionLocal()
    
    try:
        # Get all claims
        claims_query = select(Claim)
        if cluster_id:
            claims_query = claims_query.where(Claim.cluster_id == cluster_id)
        
        claims_result = await session.execute(claims_query)
        claims = claims_result.scalars().all()
        
        total_claims = len(claims)
        
        if total_claims == 0:
            return EvidenceCoverageResult(
                total_claims=0,
                claims_with_evidence=0,
                claims_without_evidence=0,
                coverage_rate=0.0,
                avg_evidence_per_claim=0.0,
                min_evidence_count=0,
                max_evidence_count=0,
                coverage_by_type=[],
                calculated_at=datetime.utcnow(),
            )
        
        # Count evidence per claim
        evidence_counts: Dict[str, int] = {}
        claim_types: Dict[str, str] = {}
        
        for claim in claims:
            claim_uuid = str(claim.id)
            claim_types[claim_uuid] = claim.claim_type
            
            # Count evidence mappings for this claim
            count_result = await session.execute(
                select(func.count()).select_from(ClaimEvidenceMap).where(
                    ClaimEvidenceMap.claim_id == claim.id
                )
            )
            evidence_counts[claim_uuid] = int(count_result.scalar() or 0)
        
        # Calculate metrics
        claims_with_evidence = sum(1 for c in evidence_counts.values() if c >= min_evidence_count)
        claims_without_evidence = total_claims - claims_with_evidence
        coverage_rate = claims_with_evidence / total_claims if total_claims > 0 else 0.0
        
        all_counts = list(evidence_counts.values())
        avg_evidence = sum(all_counts) / len(all_counts) if all_counts else 0.0
        min_count = min(all_counts) if all_counts else 0
        max_count = max(all_counts) if all_counts else 0
        
        # Coverage by claim type
        type_stats: Dict[str, Dict[str, int]] = {}
        for claim_uuid, count in evidence_counts.items():
            claim_type = claim_types.get(claim_uuid, "unknown")
            if claim_type not in type_stats:
                type_stats[claim_type] = {"total": 0, "with_evidence": 0}
            type_stats[claim_type]["total"] += 1
            if count >= min_evidence_count:
                type_stats[claim_type]["with_evidence"] += 1
        
        coverage_by_type = [
            CoverageByType(
                claim_type=claim_type,
                total_claims=stats["total"],
                claims_with_evidence=stats["with_evidence"],
                coverage_rate=stats["with_evidence"] / stats["total"] if stats["total"] > 0 else 0.0,
            )
            for claim_type, stats in sorted(type_stats.items())
        ]
        
        return EvidenceCoverageResult(
            total_claims=total_claims,
            claims_with_evidence=claims_with_evidence,
            claims_without_evidence=claims_without_evidence,
            coverage_rate=round(coverage_rate, 4),
            avg_evidence_per_claim=round(avg_evidence, 2),
            min_evidence_count=min_count,
            max_evidence_count=max_count,
            coverage_by_type=coverage_by_type,
            calculated_at=datetime.utcnow(),
        )
    finally:
        if close_session:
            await session.close()


async def get_claims_without_evidence(
    limit: int = 50,
    *,
    cluster_id: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Get list of claims that have no evidence mappings.
    
    Useful for identifying gaps in evidence coverage.
    """
    async with AsyncSessionLocal() as session:
        claims_query = select(Claim)
        if cluster_id:
            claims_query = claims_query.where(Claim.cluster_id == cluster_id)
        
        claims_result = await session.execute(claims_query)
        claims = claims_result.scalars().all()
        
        uncovered = []
        for claim in claims:
            count_result = await session.execute(
                select(func.count()).select_from(ClaimEvidenceMap).where(
                    ClaimEvidenceMap.claim_id == claim.id
                )
            )
            if int(count_result.scalar() or 0) == 0:
                uncovered.append({
                    "claim_id": claim.claim_id,
                    "claim_type": claim.claim_type,
                    "statement": claim.statement[:100] + "..." if len(claim.statement) > 100 else claim.statement,
                    "cluster_id": claim.cluster_id or "-",
                })
                if len(uncovered) >= limit:
                    break
        
        return uncovered
