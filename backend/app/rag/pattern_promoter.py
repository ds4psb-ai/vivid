"""Pattern Promoter: Evidence → Pattern Promotion Scheduler.

성공적인 캡슐 실행 결과(Evidence)를 상위 계층으로 프로모션.
- Weekly: Tier2 → Tier1 (앱별 → 차원별)
- Monthly: Tier1 → Tier0 (차원별 → NotebookLM)

Usage:
    from app.rag.pattern_promoter import get_pattern_promoter

    promoter = get_pattern_promoter()

    # 주간 프로모션 실행
    result = await promoter.run_weekly_promotion()

    # 월간 프로모션 실행
    result = await promoter.run_monthly_promotion()

    # 스케줄러 시작
    await promoter.start_scheduler()
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class PromotionType(str, Enum):
    """프로모션 타입."""
    WEEKLY = "weekly"    # Tier2 → Tier1
    MONTHLY = "monthly"  # Tier1 → Tier0


@dataclass
class PromotionConfig:
    """프로모션 설정."""
    # 프로모션 임계값
    weekly_min_quality: float = 0.75      # 주간: 품질 75% 이상
    weekly_min_usage: int = 3             # 주간: 3회 이상 사용
    monthly_min_quality: float = 0.85     # 월간: 품질 85% 이상
    monthly_min_usage: int = 10           # 월간: 10회 이상 사용

    # 배치 설정
    batch_size: int = 100
    max_promotion_per_run: int = 500

    # 스케줄 (cron 스타일)
    weekly_day: int = 0       # 월요일 (0=월)
    weekly_hour: int = 3      # 새벽 3시
    monthly_day: int = 1      # 매월 1일
    monthly_hour: int = 4     # 새벽 4시


# ============================================================================
# Promotion Candidate
# ============================================================================

@dataclass
class PromotionCandidate:
    """프로모션 후보."""
    evidence_id: str
    content: str
    dimension: str
    app_key: str
    quality_score: float
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def meets_weekly_criteria(self, config: PromotionConfig) -> bool:
        """주간 프로모션 기준 충족 여부."""
        return (
            self.quality_score >= config.weekly_min_quality and
            self.usage_count >= config.weekly_min_usage
        )

    def meets_monthly_criteria(self, config: PromotionConfig) -> bool:
        """월간 프로모션 기준 충족 여부."""
        return (
            self.quality_score >= config.monthly_min_quality and
            self.usage_count >= config.monthly_min_usage
        )


@dataclass
class PromotionResult:
    """프로모션 결과."""
    promotion_type: PromotionType
    batch_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_candidates: int = 0
    promoted_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    duration_seconds: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "promotion_type": self.promotion_type.value,
            "batch_id": self.batch_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_candidates": self.total_candidates,
            "promoted_count": self.promoted_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.promoted_count / max(self.total_candidates, 1),
        }


# ============================================================================
# Pattern Promoter
# ============================================================================

class PatternPromoter:
    """패턴 프로모션 서비스.

    Evidence 기반 지식 프로모션:
    - Weekly: Tier2 (앱별) → Tier1 (차원별 Qdrant)
    - Monthly: Tier1 (Qdrant) → Tier0 (NotebookLM)
    """

    def __init__(self, config: Optional[PromotionConfig] = None):
        """Initialize promoter.

        Args:
            config: 프로모션 설정
        """
        self.config = config or PromotionConfig()
        self._scheduler_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._last_weekly: Optional[datetime] = None
        self._last_monthly: Optional[datetime] = None
        self._promotion_history: List[PromotionResult] = []

    async def run_weekly_promotion(self) -> PromotionResult:
        """주간 프로모션 실행: Tier2 → Tier1.

        앱별 컨텍스트에서 검증된 패턴을 차원별 Qdrant로 프로모션.

        Returns:
            PromotionResult
        """
        import time
        from uuid import uuid4

        batch_id = f"weekly_{uuid4().hex[:8]}"
        start_time = time.monotonic()
        result = PromotionResult(
            promotion_type=PromotionType.WEEKLY,
            batch_id=batch_id,
            started_at=datetime.utcnow(),
        )

        logger.info(f"[Promoter] Starting weekly promotion: {batch_id}")

        try:
            # 1. 프로모션 후보 수집
            candidates = await self._collect_weekly_candidates()
            result.total_candidates = len(candidates)

            if not candidates:
                logger.info("[Promoter] No weekly promotion candidates found")
                result.completed_at = datetime.utcnow()
                result.duration_seconds = int(time.monotonic() - start_time)
                self._last_weekly = datetime.utcnow()
                return result

            # 2. 프로모션 실행
            for candidate in candidates[:self.config.max_promotion_per_run]:
                try:
                    success = await self._promote_to_tier1(candidate)
                    if success:
                        result.promoted_count += 1
                    else:
                        result.skipped_count += 1
                except Exception as e:
                    result.failed_count += 1
                    result.errors.append(f"{candidate.evidence_id}: {str(e)}")
                    logger.error(f"[Promoter] Weekly promotion error: {e}")

            result.completed_at = datetime.utcnow()
            result.duration_seconds = int(time.monotonic() - start_time)
            self._last_weekly = datetime.utcnow()
            self._promotion_history.append(result)

            logger.info(
                f"[Promoter] Weekly promotion completed: "
                f"{result.promoted_count}/{result.total_candidates} promoted"
            )

        except Exception as e:
            result.errors.append(f"Critical error: {str(e)}")
            result.completed_at = datetime.utcnow()
            result.duration_seconds = int(time.monotonic() - start_time)
            logger.exception(f"[Promoter] Weekly promotion failed: {e}")

        return result

    async def run_monthly_promotion(self) -> PromotionResult:
        """월간 프로모션 실행: Tier1 → Tier0.

        차원별 Qdrant에서 가장 성공적인 패턴을 NotebookLM으로 프로모션.

        Returns:
            PromotionResult
        """
        import time
        from uuid import uuid4

        batch_id = f"monthly_{uuid4().hex[:8]}"
        start_time = time.monotonic()
        result = PromotionResult(
            promotion_type=PromotionType.MONTHLY,
            batch_id=batch_id,
            started_at=datetime.utcnow(),
        )

        logger.info(f"[Promoter] Starting monthly promotion: {batch_id}")

        try:
            # 1. 프로모션 후보 수집
            candidates = await self._collect_monthly_candidates()
            result.total_candidates = len(candidates)

            if not candidates:
                logger.info("[Promoter] No monthly promotion candidates found")
                result.completed_at = datetime.utcnow()
                result.duration_seconds = int(time.monotonic() - start_time)
                self._last_monthly = datetime.utcnow()
                return result

            # 2. 프로모션 실행
            for candidate in candidates[:self.config.max_promotion_per_run]:
                try:
                    success = await self._promote_to_tier0(candidate)
                    if success:
                        result.promoted_count += 1
                    else:
                        result.skipped_count += 1
                except Exception as e:
                    result.failed_count += 1
                    result.errors.append(f"{candidate.evidence_id}: {str(e)}")
                    logger.error(f"[Promoter] Monthly promotion error: {e}")

            result.completed_at = datetime.utcnow()
            result.duration_seconds = int(time.monotonic() - start_time)
            self._last_monthly = datetime.utcnow()
            self._promotion_history.append(result)

            logger.info(
                f"[Promoter] Monthly promotion completed: "
                f"{result.promoted_count}/{result.total_candidates} promoted"
            )

        except Exception as e:
            result.errors.append(f"Critical error: {str(e)}")
            result.completed_at = datetime.utcnow()
            result.duration_seconds = int(time.monotonic() - start_time)
            logger.exception(f"[Promoter] Monthly promotion failed: {e}")

        return result

    async def _collect_weekly_candidates(self) -> List[PromotionCandidate]:
        """주간 프로모션 후보 수집.

        피드백 루프에서 인덱싱된 Evidence 중 기준 충족하는 것들.
        """
        candidates: List[PromotionCandidate] = []

        try:
            from app.rag.feedback_loop import get_feedback_loop

            feedback_loop = get_feedback_loop()
            # 실제 구현 시 DB/Redis에서 Evidence 조회
            # 현재는 시뮬레이션

            logger.debug("[Promoter] Collecting weekly candidates from feedback loop")

            # 시뮬레이션: 실제 구현 시 Evidence DB 조회
            # candidates = await feedback_loop.get_pending_evidence(
            #     min_quality=self.config.weekly_min_quality,
            #     min_usage=self.config.weekly_min_usage,
            #     limit=self.config.batch_size,
            # )

        except ImportError:
            logger.warning("[Promoter] Feedback loop not available")
        except Exception as e:
            logger.error(f"[Promoter] Error collecting weekly candidates: {e}")

        return candidates

    async def _collect_monthly_candidates(self) -> List[PromotionCandidate]:
        """월간 프로모션 후보 수집.

        Tier1 Qdrant에서 가장 성공적인 문서들.
        """
        candidates: List[PromotionCandidate] = []

        try:
            from app.rag.tier1_dimension_rag import get_dimension_rag

            # 각 차원에서 상위 품질 문서 수집
            dimensions = ["1D", "2D", "3D", "4D", "AD", "QC"]

            for dim in dimensions:
                try:
                    rag = get_dimension_rag(dim)
                    # 실제 구현 시 품질 점수 기반 상위 문서 조회
                    # top_docs = rag.get_top_quality_documents(
                    #     min_quality=self.config.monthly_min_quality,
                    #     limit=10,
                    # )
                    # candidates.extend(top_docs)
                except Exception as e:
                    logger.error(f"[Promoter] Error collecting from {dim}: {e}")

        except ImportError:
            logger.warning("[Promoter] Tier1 RAG not available")
        except Exception as e:
            logger.error(f"[Promoter] Error collecting monthly candidates: {e}")

        return candidates

    async def _promote_to_tier1(self, candidate: PromotionCandidate) -> bool:
        """Tier1 (차원별 Qdrant)로 프로모션.

        Args:
            candidate: 프로모션 후보

        Returns:
            True if successful
        """
        try:
            from app.rag.tier1_dimension_rag import get_dimension_rag

            rag = get_dimension_rag(candidate.dimension)

            # 문서 인덱싱
            success = rag.index_document(
                doc_id=f"promoted_{candidate.evidence_id}",
                content=candidate.content,
                metadata={
                    "source": "promotion",
                    "promotion_type": "weekly",
                    "app_key": candidate.app_key,
                    "quality_score": candidate.quality_score,
                    "usage_count": candidate.usage_count,
                    "promoted_at": datetime.utcnow().isoformat(),
                },
            )

            if success:
                logger.debug(
                    f"[Promoter] Promoted {candidate.evidence_id} → {candidate.dimension}"
                )

            return success

        except Exception as e:
            logger.error(f"[Promoter] Tier1 promotion error: {e}")
            return False

    async def _promote_to_tier0(self, candidate: PromotionCandidate) -> bool:
        """Tier0 (NotebookLM)로 프로모션.

        NotebookLM은 읽기 전용이므로, 실제로는 관리자 리뷰 큐에 추가.

        Args:
            candidate: 프로모션 후보

        Returns:
            True if queued for review
        """
        try:
            # NotebookLM은 직접 인덱싱 불가
            # 관리자 리뷰 큐에 추가
            logger.info(
                f"[Promoter] Queued for NotebookLM review: {candidate.evidence_id} "
                f"(quality={candidate.quality_score:.2f}, usage={candidate.usage_count})"
            )

            # 실제 구현 시:
            # await review_queue.add(candidate)

            return True

        except Exception as e:
            logger.error(f"[Promoter] Tier0 promotion error: {e}")
            return False

    async def start_scheduler(self) -> None:
        """스케줄러 시작."""
        if self._scheduler_task is not None:
            logger.warning("[Promoter] Scheduler already running")
            return

        self._is_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("[Promoter] Scheduler started")

    async def stop_scheduler(self) -> None:
        """스케줄러 중지."""
        self._is_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
        logger.info("[Promoter] Scheduler stopped")

    async def _scheduler_loop(self) -> None:
        """스케줄러 루프."""
        while self._is_running:
            try:
                now = datetime.utcnow()

                # 주간 프로모션 체크
                if self._should_run_weekly(now):
                    await self.run_weekly_promotion()

                # 월간 프로모션 체크
                if self._should_run_monthly(now):
                    await self.run_monthly_promotion()

                # 1시간마다 체크
                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Promoter] Scheduler error: {e}")
                await asyncio.sleep(60)  # 에러 시 1분 후 재시도

    def _should_run_weekly(self, now: datetime) -> bool:
        """주간 프로모션 실행 여부."""
        # 월요일 새벽 3시
        if now.weekday() != self.config.weekly_day:
            return False
        if now.hour != self.config.weekly_hour:
            return False
        if self._last_weekly and (now - self._last_weekly) < timedelta(hours=23):
            return False
        return True

    def _should_run_monthly(self, now: datetime) -> bool:
        """월간 프로모션 실행 여부."""
        # 매월 1일 새벽 4시
        if now.day != self.config.monthly_day:
            return False
        if now.hour != self.config.monthly_hour:
            return False
        if self._last_monthly and (now - self._last_monthly) < timedelta(hours=23):
            return False
        return True

    def get_stats(self) -> Dict[str, Any]:
        """프로모터 통계."""
        return {
            "is_running": self._is_running,
            "last_weekly": self._last_weekly.isoformat() if self._last_weekly else None,
            "last_monthly": self._last_monthly.isoformat() if self._last_monthly else None,
            "history_count": len(self._promotion_history),
            "recent_promotions": [
                r.to_dict() for r in self._promotion_history[-5:]
            ],
            "config": {
                "weekly_min_quality": self.config.weekly_min_quality,
                "weekly_min_usage": self.config.weekly_min_usage,
                "monthly_min_quality": self.config.monthly_min_quality,
                "monthly_min_usage": self.config.monthly_min_usage,
            },
        }

    def get_history(
        self,
        promotion_type: Optional[PromotionType] = None,
        limit: int = 20,
    ) -> List[PromotionResult]:
        """프로모션 히스토리 조회."""
        history = self._promotion_history
        if promotion_type:
            history = [r for r in history if r.promotion_type == promotion_type]
        return history[-limit:]


# ============================================================================
# Singleton
# ============================================================================

_pattern_promoter: Optional[PatternPromoter] = None


def get_pattern_promoter(
    config: Optional[PromotionConfig] = None,
) -> PatternPromoter:
    """패턴 프로모터 싱글톤 반환.

    Args:
        config: 설정 (최초 호출 시에만 적용)

    Returns:
        PatternPromoter instance
    """
    global _pattern_promoter
    if _pattern_promoter is None:
        _pattern_promoter = PatternPromoter(config)
    return _pattern_promoter


def reset_pattern_promoter() -> None:
    """프로모터 리셋 (테스트용)."""
    global _pattern_promoter
    if _pattern_promoter:
        asyncio.create_task(_pattern_promoter.stop_scheduler())
    _pattern_promoter = None
