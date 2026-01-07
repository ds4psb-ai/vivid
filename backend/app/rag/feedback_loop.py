"""
RAG Feedback Loop: Evidence → Qdrant 인덱싱.

성공적인 캡슐 실행 결과(Evidence)를 Qdrant에 인덱싱하여
미래 RAG 검색 품질을 향상시키는 피드백 루프.

IMPORTANT: "생성 완료 ≠ 좋은 품질"
- AI 품질 평가 (QualityEvaluator) 필수
- 사용자 승인 (user_accepted) 필수
- is_promotion_eligible: overall >= 0.85 AND user_accepted

Usage:
    from app.rag.feedback_loop import FeedbackLoopRAG, get_feedback_loop

    loop = get_feedback_loop()

    # 캡슐 실행 결과 평가 및 인덱싱
    result = await loop.process_capsule_result(
        capsule_id="dimension.aesthetic.direct",
        inputs={"concept": "bong style"},
        output={"visual_guidelines": "..."},
        session_id="session_123",
    )

    # 사용자 피드백 수신 후 승격
    await loop.handle_user_feedback(
        session_id="session_123",
        evidence_id=result["evidence_id"],
        accepted=True,
        rating=4.5,
    )

    # 통계 조회
    stats = loop.get_stats()
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.rag.tier1_dimension_rag import get_dimension_rag
from app.rag.app_manifest import get_manifest, APP_MANIFESTS
from app.rag.quality_criteria import QualityCriteria, classify_quality_level
from app.rag.quality_evaluator import get_quality_evaluator

logger = logging.getLogger(__name__)


@dataclass
class EvidenceRecord:
    """인덱싱할 Evidence 레코드.

    Attributes:
        capsule_id: 캡슐 식별자
        dimension: 타겟 차원
        content: 인덱싱할 콘텐츠
        inputs_summary: 입력 요약
        quality: QualityCriteria 객체 (7차원 품질 평가)
        quality_score: 품질 점수 (0-1) - deprecated, use quality.overall
        metadata: 추가 메타데이터
        timestamp: 생성 시간
        status: pending | indexed | promoted | rejected
    """
    capsule_id: str
    dimension: str
    content: str
    inputs_summary: str = ""
    quality: Optional[QualityCriteria] = None
    quality_score: float = 0.0  # Backward compatibility
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"  # pending | indexed | promoted | rejected

    def __post_init__(self):
        """Sync quality_score with quality.overall if available."""
        if self.quality is not None:
            self.quality_score = self.quality.overall

    def generate_doc_id(self) -> str:
        """고유 문서 ID 생성."""
        hash_input = f"{self.capsule_id}:{self.content[:200]}:{self.timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    @property
    def is_promotion_eligible(self) -> bool:
        """Check if eligible for pattern promotion."""
        if self.quality is None:
            return False
        return self.quality.is_promotion_eligible

    @property
    def is_indexable(self) -> bool:
        """Check if should be indexed to RAG."""
        if self.quality is None:
            return self.quality_score >= 0.70  # Fallback
        return self.quality.is_indexable


class FeedbackLoopRAG:
    """RAG 피드백 루프 서비스 (v2 - QualityEvaluator 통합).

    IMPORTANT: "생성 완료 ≠ 좋은 품질"

    Flow:
    1. process_capsule_result() - AI 품질 평가 수행
    2. handle_user_feedback() - 사용자 승인 대기
    3. is_promotion_eligible 판단 - overall >= 0.85 AND user_accepted
    4. 승격 자격 시 _store_success_pattern() 호출

    Features:
    - QualityEvaluator 통합 (7차원 품질 평가)
    - 사용자 피드백 필수 (user_accepted)
    - Pending evidence 관리
    - 배치 인덱싱 지원
    """

    # 인덱싱 임계값 (is_indexable: overall >= 0.70)
    MIN_INDEX_THRESHOLD = 0.70
    # 레거시 호환성 별칭 (deprecated: use MIN_INDEX_THRESHOLD)
    MIN_QUALITY_THRESHOLD = 0.70
    # 승격 임계값 (is_promotion_eligible: overall >= 0.85 AND user_accepted)
    MIN_PROMOTION_THRESHOLD = 0.85

    # 캡슐 ID → 타겟 차원 매핑
    CAPSULE_TO_DIMENSION = {
        "teaching.prompt.generate": "1D",
        "teaching.storyboard.create": "2D",
        "teaching.image.generate": "3D",
        "teaching.reference.analyze": "4D",
        "dimension.quality.check": "QC",
        "dimension.aesthetic.direct": "AD",
        "dimension.persona.analyze": "AI",
        "veo.video.generate": "VEO",
        # Dimension API v2
        "dimension.1d.generate": "1D",
        "dimension.2d.create": "2D",
        "dimension.3d.generate": "3D",
        "dimension.4d.analyze": "4D",
    }

    def __init__(self):
        """Initialize feedback loop."""
        self._evaluator = get_quality_evaluator()
        self._pending_evidence: Dict[str, EvidenceRecord] = {}  # evidence_id → record
        self._indexed_count = 0
        self._promoted_count = 0
        self._skipped_count = 0
        self._error_count = 0

    async def process_capsule_result(
        self,
        capsule_id: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """캡슐 실행 결과 처리 (AI 품질 평가 수행).

        Step 1 of the flow: Evaluate quality with Gemini.
        Does NOT index yet - waits for user feedback.

        Args:
            capsule_id: 캡슐 식별자
            inputs: 캡슐 입력
            output: 캡슐 출력
            session_id: 세션 ID (피드백 추적용)
            user_id: 사용자 ID

        Returns:
            {
                "evidence_id": str,
                "quality": QualityCriteria.to_dict(),
                "quality_level": str,
                "pending_feedback": True,
            }
        """
        # 타겟 차원 결정
        dimension = self._get_dimension(capsule_id)
        if not dimension:
            logger.warning(f"[FeedbackLoopRAG] Unknown capsule: {capsule_id}")
            self._skipped_count += 1
            return {"error": f"Unknown capsule: {capsule_id}"}

        # AI 품질 평가 수행
        quality = await self._evaluator.evaluate(
            dimension=dimension,
            input_request=inputs,
            output_result=output,
        )

        # 인덱싱할 콘텐츠 추출
        content = self._extract_indexable_content(capsule_id, inputs, output)
        if not content or len(content) < 20:
            logger.debug(f"[FeedbackLoopRAG] Skipping {capsule_id}: insufficient content")
            self._skipped_count += 1
            return {"error": "Insufficient content"}

        # Evidence 레코드 생성
        record = EvidenceRecord(
            capsule_id=capsule_id,
            dimension=dimension,
            content=content,
            inputs_summary=str(inputs)[:200],
            quality=quality,
            metadata={
                "source": "feedback_loop_v2",
                "app_key": capsule_id,
                "session_id": session_id,
                "user_id_hash": hashlib.md5(
                    (user_id or "anonymous").encode()
                ).hexdigest()[:8],
            },
            status="pending",
        )

        # Pending에 저장 (사용자 피드백 대기)
        evidence_id = record.generate_doc_id()
        self._pending_evidence[evidence_id] = record

        logger.info(
            f"[FeedbackLoopRAG] Processed {capsule_id}: "
            f"overall={quality.overall:.2f}, level={classify_quality_level(quality.overall)}, "
            f"pending_feedback=True"
        )

        return {
            "evidence_id": evidence_id,
            "quality": quality.to_dict(),
            "quality_level": classify_quality_level(quality.overall),
            "pending_feedback": True,
            "is_indexable": quality.is_indexable,
        }

    async def handle_user_feedback(
        self,
        session_id: str,
        evidence_id: str,
        accepted: bool,
        rating: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """사용자 피드백 처리 후 인덱싱/승격 결정.

        Step 2 of the flow: Apply user feedback and decide action.

        Args:
            session_id: 세션 ID
            evidence_id: Evidence ID
            accepted: 사용자 승인 여부
            rating: 사용자 평점 (1-5)
            comment: 사용자 코멘트

        Returns:
            {
                "action": "indexed" | "promoted" | "rejected",
                "quality": updated QualityCriteria,
            }
        """
        # Pending evidence 조회
        record = self._pending_evidence.get(evidence_id)
        if not record:
            logger.warning(f"[FeedbackLoopRAG] Evidence not found: {evidence_id}")
            return {"error": f"Evidence not found: {evidence_id}"}

        # 사용자 피드백 적용
        user_feedback = {
            "accepted": accepted,
            "rating": rating,
            "comment": comment,
        }
        record.quality = self._evaluator.update_with_user_feedback(
            record.quality, user_feedback
        )

        # 행동 결정
        action = "rejected"

        if record.is_promotion_eligible:
            # 승격 자격: overall >= 0.85 AND user_accepted
            success = await self._store_success_pattern(record)
            if success:
                action = "promoted"
                self._promoted_count += 1
                record.status = "promoted"
        elif record.is_indexable:
            # 인덱싱 자격: overall >= 0.70
            success = self._index_to_qdrant(record)
            if success:
                action = "indexed"
                self._indexed_count += 1
                record.status = "indexed"
        else:
            record.status = "rejected"
            self._skipped_count += 1

        # Pending에서 제거
        del self._pending_evidence[evidence_id]

        logger.info(
            f"[FeedbackLoopRAG] Feedback processed: {evidence_id} → {action} "
            f"(user_accepted={accepted}, overall={record.quality.overall:.2f})"
        )

        return {
            "action": action,
            "evidence_id": evidence_id,
            "quality": record.quality.to_dict(),
        }

    def _get_dimension(self, capsule_id: str) -> Optional[str]:
        """Get target dimension for capsule."""
        dimension = self.CAPSULE_TO_DIMENSION.get(capsule_id)
        if not dimension:
            manifest = get_manifest(capsule_id)
            if manifest and manifest.dimensions:
                dimension = manifest.dimensions[0]
        return dimension

    async def _store_success_pattern(self, record: EvidenceRecord) -> bool:
        """승격 자격 달성 시 성공 패턴 저장.

        Args:
            record: Evidence 레코드

        Returns:
            True if stored successfully
        """
        # 1. Qdrant에 인덱싱 (높은 우선순위)
        success = self._index_to_qdrant(record, promoted=True)

        # 2. LightRAG에도 인덱싱 (그래프 구조)
        try:
            from app.rag.lightrag_adapter import get_lightrag_adapter
            adapter = get_lightrag_adapter()
            await adapter.index_document(
                doc_id=f"promoted_{record.generate_doc_id()}",
                content=record.content,
                dimension=record.dimension,
                metadata={
                    **record.metadata,
                    "promoted": True,
                    "quality_score": record.quality.overall,
                },
            )
        except Exception as e:
            logger.warning(f"[FeedbackLoopRAG] LightRAG index failed: {e}")

        logger.info(
            f"[FeedbackLoopRAG] SUCCESS PATTERN stored: {record.capsule_id} "
            f"→ {record.dimension} (quality={record.quality.overall:.2f})"
        )

        return success

    def _index_to_qdrant(
        self,
        record: EvidenceRecord,
        promoted: bool = False,
    ) -> bool:
        """Qdrant에 인덱싱.

        Args:
            record: Evidence 레코드
            promoted: 승격된 패턴 여부

        Returns:
            True if indexed successfully
        """
        try:
            rag = get_dimension_rag(record.dimension)
            return rag.index_document(
                doc_id=record.generate_doc_id(),
                content=record.content,
                metadata={
                    **record.metadata,
                    "quality_score": record.quality.overall if record.quality else record.quality_score,
                    "quality_level": classify_quality_level(record.quality.overall) if record.quality else "unknown",
                    "promoted": promoted,
                    "user_accepted": record.quality.user_accepted if record.quality else False,
                },
            )
        except Exception as e:
            logger.error(f"[FeedbackLoopRAG] Qdrant index error: {e}")
            self._error_count += 1
            return False

    def _extract_indexable_content(
        self,
        capsule_id: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
    ) -> str:
        """캡슐 출력에서 인덱싱할 콘텐츠 추출.

        Args:
            capsule_id: 캡슐 식별자
            inputs: 캡슐 입력
            output: 캡슐 출력

        Returns:
            인덱싱할 텍스트 콘텐츠
        """
        parts = []

        # 입력 요약 추가
        if inputs.get("topic"):
            parts.append(f"Topic: {inputs['topic']}")
        if inputs.get("concept"):
            parts.append(f"Concept: {inputs['concept']}")
        if inputs.get("description"):
            parts.append(f"Description: {inputs['description']}")

        # 출력 콘텐츠 추가
        if capsule_id == "teaching.prompt.generate":
            if output.get("prompt"):
                parts.append(f"Generated Prompt: {output['prompt']}")
            if output.get("style"):
                style = output["style"]
                if isinstance(style, dict):
                    parts.append(f"Style: {style.get('cinematography', '')} {style.get('lighting', '')}")

        elif capsule_id == "teaching.storyboard.create":
            scenes = output.get("scenes", [])
            if scenes and isinstance(scenes, list):
                for i, scene in enumerate(scenes[:5], 1):
                    if isinstance(scene, dict):
                        parts.append(f"Scene {i}: {scene.get('description', '')}")

        elif capsule_id == "teaching.image.generate":
            if output.get("prompt"):
                parts.append(f"Image Prompt: {output['prompt']}")
            if output.get("style_tags"):
                parts.append(f"Style Tags: {', '.join(output['style_tags'])}")

        elif capsule_id == "teaching.reference.analyze":
            if output.get("analysis"):
                parts.append(f"Analysis: {output['analysis']}")
            if output.get("techniques"):
                parts.append(f"Techniques: {', '.join(output.get('techniques', []))}")

        elif capsule_id == "dimension.aesthetic.direct":
            if output.get("visual_guidelines"):
                parts.append(f"Guidelines: {output['visual_guidelines']}")
            if output.get("style_keywords"):
                keywords = output["style_keywords"]
                if isinstance(keywords, list):
                    parts.append(f"Keywords: {', '.join(keywords)}")
            if output.get("color_palette"):
                palette = output["color_palette"]
                if isinstance(palette, list):
                    parts.append(f"Palette: {', '.join(palette)}")

        elif capsule_id == "dimension.quality.check":
            if output.get("suggestions"):
                suggestions = output["suggestions"]
                if isinstance(suggestions, list):
                    parts.append(f"Suggestions: {'; '.join(suggestions[:3])}")

        elif capsule_id == "dimension.persona.analyze":
            if output.get("persona_update"):
                update = output["persona_update"]
                if isinstance(update, dict):
                    for k, v in list(update.items())[:5]:
                        parts.append(f"{k}: {v}")

        elif capsule_id == "veo.video.generate":
            if output.get("prompt"):
                parts.append(f"Veo Prompt: {output['prompt']}")

        # 폴백: 직접 출력 텍스트 사용
        if not parts:
            if isinstance(output, str):
                parts.append(output[:1000])
            elif isinstance(output, dict):
                for key in ["prompt", "content", "result", "text", "description"]:
                    if key in output and output[key]:
                        parts.append(f"{key}: {str(output[key])[:500]}")
                        break

        return "\n".join(parts)

    def index_capsule_result(
        self,
        capsule_id: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
        quality_score: float = 0.8,
        user_id: Optional[str] = None,
    ) -> bool:
        """캡슐 실행 결과를 RAG에 인덱싱.

        Args:
            capsule_id: 캡슐 식별자
            inputs: 캡슐 입력
            output: 캡슐 출력
            quality_score: 품질 점수 (0-1, 기본 0.8)
            user_id: 사용자 ID (익명화됨)

        Returns:
            True if indexed successfully
        """
        # 품질 임계값 확인
        if quality_score < self.MIN_QUALITY_THRESHOLD:
            logger.debug(
                f"[FeedbackLoop] Skipping {capsule_id}: "
                f"quality {quality_score} < {self.MIN_QUALITY_THRESHOLD}"
            )
            self._skipped_count += 1
            return False

        # 타겟 차원 결정
        dimension = self.CAPSULE_TO_DIMENSION.get(capsule_id)
        if not dimension:
            # 매니페스트에서 첫 번째 차원 사용
            manifest = get_manifest(capsule_id)
            if manifest and manifest.dimensions:
                dimension = manifest.dimensions[0]
            else:
                logger.warning(f"[FeedbackLoop] Unknown capsule: {capsule_id}")
                self._skipped_count += 1
                return False

        # 인덱싱할 콘텐츠 추출
        content = self._extract_indexable_content(capsule_id, inputs, output)
        if not content or len(content) < 20:
            logger.debug(f"[FeedbackLoop] Skipping {capsule_id}: insufficient content")
            self._skipped_count += 1
            return False

        # Evidence 레코드 생성
        record = EvidenceRecord(
            capsule_id=capsule_id,
            dimension=dimension,
            content=content,
            inputs_summary=str(inputs)[:200],
            quality_score=quality_score,
            metadata={
                "source": "feedback_loop",
                "app_key": capsule_id,
                "quality_score": quality_score,
                "user_id_hash": hashlib.md5(
                    (user_id or "anonymous").encode()
                ).hexdigest()[:8],
            },
        )

        # Qdrant에 인덱싱
        try:
            rag = get_dimension_rag(dimension)
            success = rag.index_document(
                doc_id=record.generate_doc_id(),
                content=record.content,
                metadata=record.metadata,
            )

            if success:
                self._indexed_count += 1
                logger.info(
                    f"[FeedbackLoop] Indexed {capsule_id} → {dimension} "
                    f"(quality={quality_score:.2f})"
                )
                return True
            else:
                self._error_count += 1
                return False

        except Exception as e:
            logger.error(f"[FeedbackLoop] Index error for {capsule_id}: {e}")
            self._error_count += 1
            return False

    def index_batch(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """배치 인덱싱.

        Args:
            results: 인덱싱할 결과 리스트
                     [{"capsule_id": ..., "inputs": ..., "output": ..., "quality_score": ...}, ...]

        Returns:
            {"indexed": N, "skipped": M, "errors": K}
        """
        indexed = 0
        skipped = 0
        errors = 0

        for result in results:
            try:
                success = self.index_capsule_result(
                    capsule_id=result.get("capsule_id", ""),
                    inputs=result.get("inputs", {}),
                    output=result.get("output", {}),
                    quality_score=result.get("quality_score", 0.8),
                    user_id=result.get("user_id"),
                )
                if success:
                    indexed += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"[FeedbackLoop] Batch item error: {e}")
                errors += 1

        return {"indexed": indexed, "skipped": skipped, "errors": errors}

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회.

        Returns:
            {
                "total_indexed": N,
                "total_skipped": M,
                "total_errors": K,
                "quality_threshold": 0.7,
                "supported_capsules": [...],
            }
        """
        return {
            "total_indexed": self._indexed_count,
            "total_skipped": self._skipped_count,
            "total_errors": self._error_count,
            "quality_threshold": self.MIN_QUALITY_THRESHOLD,
            "supported_capsules": list(self.CAPSULE_TO_DIMENSION.keys()),
        }

    def reset_stats(self) -> None:
        """통계 리셋."""
        self._indexed_count = 0
        self._skipped_count = 0
        self._error_count = 0


# 싱글톤 인스턴스
_feedback_loop_instance: Optional[FeedbackLoopRAG] = None


def get_feedback_loop() -> FeedbackLoopRAG:
    """피드백 루프 싱글톤 반환.

    Returns:
        FeedbackLoopRAG instance
    """
    global _feedback_loop_instance
    if _feedback_loop_instance is None:
        _feedback_loop_instance = FeedbackLoopRAG()
    return _feedback_loop_instance


# 하위 호환성 별칭 (deprecated: use FeedbackLoopRAG)
FeedbackLoop = FeedbackLoopRAG


def index_successful_result(
    capsule_id: str,
    inputs: Dict[str, Any],
    output: Dict[str, Any],
    quality_score: float = 0.8,
    user_id: Optional[str] = None,
) -> bool:
    """Convenience function: 성공한 결과 인덱싱.

    Args:
        capsule_id: 캡슐 식별자
        inputs: 캡슐 입력
        output: 캡슐 출력
        quality_score: 품질 점수
        user_id: 사용자 ID

    Returns:
        True if indexed
    """
    loop = get_feedback_loop()
    return loop.index_capsule_result(
        capsule_id=capsule_id,
        inputs=inputs,
        output=output,
        quality_score=quality_score,
        user_id=user_id,
    )
