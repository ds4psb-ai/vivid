"""Feedback Loop Service (Phase 7 HITL Enhancement).

사용자 피드백을 RAG 지식베이스에 자동 반영하는 서비스.

2026 Best Practices:
- Feedback → RAG: 사용자 피드백으로 지속적 학습
- CRAG Pattern: Corrective RAG for negative feedback
- Apple ML RL + RAG: Reinforcement learning integrated with retrieval

Usage:
    from app.services.feedback_loop import FeedbackLoopService

    service = FeedbackLoopService(db)

    # 긍정 피드백 처리 (평점 >= 4)
    result = await service.process_positive_feedback(feedback, rag_response)

    # 부정 피드백 처리
    result = await service.process_negative_feedback(feedback, rag_response)

    # 일일 학습 사이클
    result = await service.aggregate_learning_cycle("cycle_2026-01-20")
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_feedback import (
    RAGResponse,
    RAGFeedback,
    FeedbackCorrection,
    FeedbackIngestion,
    CorrectionType,
)
from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Result Dataclasses
# =============================================================================

@dataclass
class FeedbackIngestionResult:
    """긍정 피드백 수집 결과."""
    feedback_id: uuid.UUID
    success: bool
    ingestion_id: Optional[uuid.UUID] = None
    qdrant_point_id: Optional[str] = None
    collection_name: Optional[str] = None
    error: Optional[str] = None


@dataclass
class FeedbackActionResult:
    """부정 피드백 처리 결과."""
    feedback_id: uuid.UUID
    correction_id: Optional[uuid.UUID] = None
    correction_type: Optional[str] = None
    cache_invalidated: bool = False
    source_flagged: bool = False
    crag_triggered: bool = False
    error: Optional[str] = None


@dataclass
class LearningCycleResult:
    """학습 사이클 결과."""
    cycle_id: str
    processed_count: int
    ingested_count: int
    corrected_count: int
    skipped_count: int
    error_count: int
    dimension_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    duration_seconds: float = 0.0


# =============================================================================
# Feedback Loop Service
# =============================================================================

class FeedbackLoopService:
    """사용자 피드백 기반 지속적 학습 서비스.

    긍정 피드백 (rating >= 4):
        1. 원본 응답에서 핵심 콘텐츠 추출
        2. SentenceTransformer로 임베딩 생성
        3. 적절한 차원 컬렉션에 Qdrant 인덱싱
        4. 메타데이터: user_validated=True

    부정 피드백:
        1. 소스 문서 검토 플래그
        2. feedback_corrections 테이블 로깅
        3. 시맨틱 캐시 항목 조정
        4. CRAG 교정 트리거 (패턴 감지 시)

    Attributes:
        db: 비동기 DB 세션
        min_rating_for_ingestion: 수집 최소 평점 (기본: 4)
        max_rating_for_correction: 교정 최대 평점 (기본: 2)
    """

    MIN_RATING_FOR_INGESTION = 4
    MAX_RATING_FOR_CORRECTION = 2

    def __init__(
        self,
        db: AsyncSession,
        min_rating_for_ingestion: int = 4,
        max_rating_for_correction: int = 2,
    ) -> None:
        """Initialize feedback loop service.

        Args:
            db: 비동기 DB 세션
            min_rating_for_ingestion: 수집 최소 평점
            max_rating_for_correction: 교정 최대 평점
        """
        self._db = db
        self.min_rating_for_ingestion = min_rating_for_ingestion
        self.max_rating_for_correction = max_rating_for_correction

    async def process_positive_feedback(
        self,
        feedback: RAGFeedback,
        rag_response: RAGResponse,
    ) -> FeedbackIngestionResult:
        """긍정 피드백 처리 (평점 >= 4).

        Args:
            feedback: RAG 피드백 레코드
            rag_response: RAG 응답 레코드

        Returns:
            FeedbackIngestionResult: 수집 결과
        """
        # 평점 검증
        if feedback.rating is None or feedback.rating < self.min_rating_for_ingestion:
            return FeedbackIngestionResult(
                feedback_id=feedback.id,
                success=False,
                error=f"Rating {feedback.rating} below threshold {self.min_rating_for_ingestion}",
            )

        # 이미 수집된 경우
        if feedback.ingested_to_rag:
            return FeedbackIngestionResult(
                feedback_id=feedback.id,
                success=True,
                error="Already ingested",
            )

        # 차원 및 컬렉션 결정
        dimension = rag_response.dimension or "1D"
        collection_name = self._get_collection_name(dimension)

        # 콘텐츠 추출
        content = self._extract_content_for_indexing(rag_response)
        if not content or len(content) < 20:
            return FeedbackIngestionResult(
                feedback_id=feedback.id,
                success=False,
                error="Insufficient content for indexing",
            )

        # Qdrant 인덱싱
        try:
            qdrant_point_id = await self._index_to_qdrant(
                content=content,
                dimension=dimension,
                collection_name=collection_name,
                metadata={
                    "response_id": str(rag_response.id),
                    "feedback_id": str(feedback.id),
                    "query": rag_response.query[:200],
                    "rating": feedback.rating,
                    "user_validated": True,
                    "auteur_key": rag_response.auteur_key,
                    "app_key": rag_response.app_key,
                    "source": "feedback_loop_v2",
                    "ingested_at": datetime.utcnow().isoformat(),
                },
            )

            # FeedbackIngestion 레코드 생성
            ingestion = FeedbackIngestion(
                feedback_id=feedback.id,
                dimension=dimension,
                qdrant_point_id=qdrant_point_id,
                collection_name=collection_name,
                content_hash=hashlib.sha256(content.encode()).hexdigest()[:32],
                content_preview=content[:500],
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                embedding_dim=384,
                auteur_key=rag_response.auteur_key,
                user_validated=True,
            )
            self._db.add(ingestion)

            # 피드백 상태 업데이트
            feedback.ingested_to_rag = True
            feedback.processed_for_learning = True

            await self._db.flush()

            logger.info(
                f"[FeedbackLoop] Positive feedback ingested: "
                f"feedback={feedback.id} dimension={dimension} rating={feedback.rating}"
            )

            return FeedbackIngestionResult(
                feedback_id=feedback.id,
                success=True,
                ingestion_id=ingestion.id,
                qdrant_point_id=qdrant_point_id,
                collection_name=collection_name,
            )

        except Exception as e:
            logger.error(f"[FeedbackLoop] Ingestion failed: {e}")
            return FeedbackIngestionResult(
                feedback_id=feedback.id,
                success=False,
                error=str(e),
            )

    async def process_negative_feedback(
        self,
        feedback: RAGFeedback,
        rag_response: RAGResponse,
    ) -> FeedbackActionResult:
        """부정 피드백 처리.

        Args:
            feedback: RAG 피드백 레코드
            rag_response: RAG 응답 레코드

        Returns:
            FeedbackActionResult: 처리 결과
        """
        result = FeedbackActionResult(feedback_id=feedback.id)

        # 평점 검증
        if feedback.rating is not None and feedback.rating > self.max_rating_for_correction:
            result.error = f"Rating {feedback.rating} above correction threshold"
            return result

        # 이미 교정된 경우
        if feedback.correction_applied:
            result.error = "Correction already applied"
            return result

        try:
            # 1. 교정 유형 결정
            correction_type = self._determine_correction_type(feedback, rag_response)

            # 2. FeedbackCorrection 레코드 생성
            correction = FeedbackCorrection(
                response_id=rag_response.id,
                feedback_id=feedback.id,
                correction_type=correction_type,
                original_query=rag_response.query,
                correction_reason=feedback.user_comment,
                dimension=rag_response.dimension,
                auteur_key=rag_response.auteur_key,
            )
            self._db.add(correction)

            # 3. 교정 유형별 액션 수행
            if correction_type == CorrectionType.CACHE_INVALIDATED.value:
                result.cache_invalidated = await self._invalidate_semantic_cache(
                    rag_response.query_hash
                )

            if correction_type == CorrectionType.SOURCE_FLAGGED.value:
                result.source_flagged = await self._flag_source_for_review(
                    rag_response
                )

            if correction_type == CorrectionType.CRAG_TRIGGERED.value:
                result.crag_triggered = await self._trigger_crag_correction(
                    rag_response, feedback
                )

            # 4. 피드백 상태 업데이트
            feedback.correction_applied = True
            feedback.processed_for_learning = True

            await self._db.flush()

            result.correction_id = correction.id
            result.correction_type = correction_type

            logger.info(
                f"[FeedbackLoop] Negative feedback processed: "
                f"feedback={feedback.id} correction_type={correction_type}"
            )

            return result

        except Exception as e:
            logger.error(f"[FeedbackLoop] Correction failed: {e}")
            result.error = str(e)
            return result

    async def aggregate_learning_cycle(
        self,
        cycle_id: str,
        since: Optional[datetime] = None,
    ) -> LearningCycleResult:
        """일일 배치 처리 - 학습 사이클.

        Args:
            cycle_id: 학습 사이클 ID (예: "cycle_2026-01-20")
            since: 처리 시작 시점 (기본: 24시간 전)

        Returns:
            LearningCycleResult: 학습 사이클 결과
        """
        start_time = datetime.utcnow()

        if not since:
            since = datetime.utcnow() - timedelta(hours=24)

        result = LearningCycleResult(
            cycle_id=cycle_id,
            processed_count=0,
            ingested_count=0,
            corrected_count=0,
            skipped_count=0,
            error_count=0,
        )

        # 미처리 피드백 조회
        feedbacks_query = (
            select(RAGFeedback)
            .where(
                and_(
                    RAGFeedback.created_at >= since,
                    RAGFeedback.processed_for_learning == False,
                )
            )
            .order_by(RAGFeedback.created_at)
        )

        feedbacks_result = await self._db.execute(feedbacks_query)
        feedbacks = list(feedbacks_result.scalars())

        logger.info(f"[FeedbackLoop] Learning cycle {cycle_id}: {len(feedbacks)} feedbacks to process")

        for feedback in feedbacks:
            try:
                # 응답 조회
                response_result = await self._db.execute(
                    select(RAGResponse).where(RAGResponse.id == feedback.response_id)
                )
                response = response_result.scalar_one_or_none()

                if not response:
                    result.skipped_count += 1
                    continue

                result.processed_count += 1

                # 차원별 통계 초기화
                dim = response.dimension or "unknown"
                if dim not in result.dimension_stats:
                    result.dimension_stats[dim] = {
                        "ingested": 0,
                        "corrected": 0,
                        "skipped": 0,
                    }

                # 긍정 피드백 처리
                if feedback.rating and feedback.rating >= self.min_rating_for_ingestion:
                    ing_result = await self.process_positive_feedback(feedback, response)
                    if ing_result.success:
                        result.ingested_count += 1
                        result.dimension_stats[dim]["ingested"] += 1
                    else:
                        result.skipped_count += 1
                        result.dimension_stats[dim]["skipped"] += 1

                # 부정 피드백 처리
                elif feedback.rating and feedback.rating <= self.max_rating_for_correction:
                    cor_result = await self.process_negative_feedback(feedback, response)
                    if cor_result.correction_id:
                        result.corrected_count += 1
                        result.dimension_stats[dim]["corrected"] += 1
                    else:
                        result.skipped_count += 1
                        result.dimension_stats[dim]["skipped"] += 1

                # 중립 피드백
                else:
                    feedback.processed_for_learning = True
                    feedback.learning_cycle_id = cycle_id
                    result.skipped_count += 1
                    result.dimension_stats[dim]["skipped"] += 1

                # 학습 사이클 ID 기록
                feedback.learning_cycle_id = cycle_id

            except Exception as e:
                logger.error(f"[FeedbackLoop] Error processing feedback {feedback.id}: {e}")
                result.error_count += 1

        await self._db.flush()

        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"[FeedbackLoop] Learning cycle completed: {cycle_id} | "
            f"processed={result.processed_count} ingested={result.ingested_count} "
            f"corrected={result.corrected_count} errors={result.error_count} "
            f"duration={result.duration_seconds:.1f}s"
        )

        return result

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_collection_name(self, dimension: str) -> str:
        """차원별 Qdrant 컬렉션 이름 반환."""
        collection_map = {
            "1D": "dimension_1d_contexts_hybrid",
            "2D": "dimension_2d_contexts_hybrid",
            "3D": "dimension_3d_contexts_hybrid",
            "4D": "dimension_4d_contexts_hybrid",
            "5D": "dimension_5d_contexts_hybrid",
            "6D": "dimension_6d_contexts_hybrid",
            "QC": "dimension_qc_contexts_hybrid",
            "AD": "dimension_ad_contexts_hybrid",
            "AI": "dimension_ai_contexts_hybrid",
            "VEO": "dimension_veo_contexts_hybrid",
        }
        return collection_map.get(dimension, "dimension_1d_contexts_hybrid")

    def _extract_content_for_indexing(self, response: RAGResponse) -> str:
        """응답에서 인덱싱할 콘텐츠 추출."""
        parts = []

        # 쿼리 추가
        if response.query:
            parts.append(f"Query: {response.query}")

        # 응답 추가
        if response.answer:
            parts.append(f"Answer: {response.answer}")

        return "\n".join(parts)

    def _determine_correction_type(
        self,
        feedback: RAGFeedback,
        response: RAGResponse,
    ) -> str:
        """교정 유형 결정."""
        # 재검색 발생 → 캐시 무효화
        if feedback.query_reformulated:
            return CorrectionType.CACHE_INVALIDATED.value

        # 소스 클릭 없음 + 낮은 평점 → 소스 검토 필요
        if not feedback.source_clicked and feedback.rating and feedback.rating <= 1:
            return CorrectionType.SOURCE_FLAGGED.value

        # CRAG 트리거 조건 (반복 패턴 감지)
        if response.crag_triggered:
            return CorrectionType.CRAG_TRIGGERED.value

        # 기본: 소스 플래그
        return CorrectionType.SOURCE_FLAGGED.value

    async def _index_to_qdrant(
        self,
        content: str,
        dimension: str,
        collection_name: str,
        metadata: Dict[str, Any],
    ) -> str:
        """Qdrant에 인덱싱.

        Returns:
            qdrant_point_id: 생성된 포인트 ID
        """
        try:
            from app.rag.tier1_dimension_rag import get_dimension_rag

            rag = get_dimension_rag(dimension)
            point_id = hashlib.md5(content.encode()).hexdigest()[:16]

            success = rag.index_document(
                doc_id=point_id,
                content=content,
                metadata=metadata,
            )

            if success:
                return point_id
            else:
                raise Exception("Qdrant indexing failed")

        except Exception as e:
            logger.error(f"[FeedbackLoop] Qdrant index error: {e}")
            raise

    async def _invalidate_semantic_cache(self, query_hash: Optional[str]) -> bool:
        """시맨틱 캐시 무효화."""
        if not query_hash:
            return False

        try:
            from app.rag.semantic_cache import get_semantic_cache

            cache = get_semantic_cache()
            if cache:
                await cache.invalidate(query_hash)
                logger.info(f"[FeedbackLoop] Cache invalidated: {query_hash}")
                return True
        except Exception as e:
            logger.warning(f"[FeedbackLoop] Cache invalidation failed: {e}")

        return False

    async def _flag_source_for_review(self, response: RAGResponse) -> bool:
        """소스 문서 검토 플래그."""
        # 소스 정보가 있으면 플래그 설정
        if response.sources:
            logger.info(
                f"[FeedbackLoop] Sources flagged for review: "
                f"response={response.id} sources={len(response.sources)}"
            )
            return True
        return False

    async def _trigger_crag_correction(
        self,
        response: RAGResponse,
        feedback: RAGFeedback,
    ) -> bool:
        """CRAG 교정 워크플로우 트리거."""
        try:
            # CRAG 교정 로직 (추후 구현)
            logger.info(
                f"[FeedbackLoop] CRAG correction triggered: "
                f"response={response.id} feedback={feedback.id}"
            )
            return True
        except Exception as e:
            logger.warning(f"[FeedbackLoop] CRAG trigger failed: {e}")
            return False

    async def get_unprocessed_feedback_count(self) -> int:
        """미처리 피드백 수 조회."""
        result = await self._db.execute(
            select(func.count())
            .select_from(RAGFeedback)
            .where(RAGFeedback.processed_for_learning == False)
        )
        return result.scalar() or 0

    async def get_learning_stats(
        self,
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """학습 통계 조회."""
        since = datetime.utcnow() - timedelta(days=period_days)

        # 총 피드백 수
        total_result = await self._db.execute(
            select(func.count())
            .select_from(RAGFeedback)
            .where(RAGFeedback.created_at >= since)
        )
        total = total_result.scalar() or 0

        # 수집된 피드백 수
        ingested_result = await self._db.execute(
            select(func.count())
            .select_from(RAGFeedback)
            .where(
                and_(
                    RAGFeedback.created_at >= since,
                    RAGFeedback.ingested_to_rag == True,
                )
            )
        )
        ingested = ingested_result.scalar() or 0

        # 교정된 피드백 수
        corrected_result = await self._db.execute(
            select(func.count())
            .select_from(RAGFeedback)
            .where(
                and_(
                    RAGFeedback.created_at >= since,
                    RAGFeedback.correction_applied == True,
                )
            )
        )
        corrected = corrected_result.scalar() or 0

        return {
            "period_days": period_days,
            "total_feedbacks": total,
            "ingested_count": ingested,
            "corrected_count": corrected,
            "pending_count": total - ingested - corrected,
            "ingestion_rate": ingested / total if total > 0 else 0.0,
            "correction_rate": corrected / total if total > 0 else 0.0,
        }
