"""
Intent Parser Service (Hardened)

자연어 → VDG 노드 속성 변환 서비스.
STPF 평가 + Kelly 권장 통합.

Hardening:
- 입력 검증 강화
- 상세 로깅
- 에러 핸들링 개선
- 성능 메트릭
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.intent_schemas import (
    NodeEditIntent, IntentType, PropertyChange, PropertyCategory,
    IntentParseRequest, IntentParseResult, IntentMapping,
    KOREAN_INTENT_MAPPINGS, COMPLEX_PATTERNS,
)
from app.schemas.stpf_schemas import STPFInputs
from app.services.stpf_engine import stpf_engine
from app.services.kelly_allocator import kelly_allocator

logger = logging.getLogger(__name__)


# =========================================================================
# Constants & Configuration
# =========================================================================

# 입력 제한
MAX_INPUT_LENGTH = 1000
MIN_INPUT_LENGTH = 2
MAX_PROPERTY_CHANGES = 20

# 신뢰도 임계값
MIN_CONFIDENCE_THRESHOLD = 0.3
HIGH_CONFIDENCE_THRESHOLD = 0.8

# STPF 임계값
STPF_DEATH_VALLEY = 250
STPF_RED_OCEAN = 500
STPF_HIGH_POTENTIAL = 800


@dataclass
class ParseMetrics:
    """파싱 성능 메트릭"""
    parse_time_ms: float
    keyword_matches: int
    total_changes: int
    is_complex: bool
    confidence: float


class IntentParserError(Exception):
    """Intent Parser 에러"""
    pass


class InputValidationError(IntentParserError):
    """입력 검증 에러"""
    pass


class ParseError(IntentParserError):
    """파싱 에러"""
    pass


class IntentParser:
    """
    자연어 → VDG 노드 속성 변환 (Hardened)
    
    Features:
    - 키워드 기반 빠른 파싱
    - 입력 검증 강화
    - STPF 평가 통합
    - 복잡한 의도 감지 (ToT 트리거)
    - 상세 로깅 및 메트릭
    """
    
    def __init__(self):
        self.mappings = list(KOREAN_INTENT_MAPPINGS)  # 복사본 사용
        self.complex_patterns = COMPLEX_PATTERNS
        self._parse_count = 0
        self._error_count = 0
        logger.info(f"IntentParser initialized with {len(self.mappings)} mappings")
    
    def parse(self, request: IntentParseRequest) -> IntentParseResult:
        """
        의도 파싱 메인 함수
        
        Args:
            request: 파싱 요청
        
        Returns:
            IntentParseResult with intent and STPF evaluation
        
        Raises:
            InputValidationError: 입력 검증 실패
            ParseError: 파싱 실패
        """
        start_time = time.time()
        self._parse_count += 1
        
        try:
            # 1. 입력 검증
            user_input = self._validate_and_sanitize_input(request.user_input)
            
            logger.debug(f"Parsing intent: '{user_input[:50]}...' (len={len(user_input)})")
            
            # 2. 복잡한 의도 감지
            is_complex, complex_description = self._detect_complex_intent(user_input)
            if is_complex:
                logger.info(f"Complex intent detected: {complex_description}")
            
            # 3. 키워드 기반 파싱
            property_changes, simple_changes, keyword_count = self._parse_keywords_with_metrics(user_input)
            
            # 4. 결과 검증
            if not property_changes and not simple_changes:
                logger.warning(f"No intent found for: '{user_input[:30]}...'")
                return IntentParseResult(
                    success=False,
                    error="의도를 파악할 수 없습니다. 더 구체적으로 말씀해주세요.",
                    parse_time_ms=(time.time() - start_time) * 1000,
                )
            
            # 5. 변경 수 제한
            if len(property_changes) > MAX_PROPERTY_CHANGES:
                logger.warning(f"Too many changes: {len(property_changes)}, truncating")
                property_changes = property_changes[:MAX_PROPERTY_CHANGES]
            
            # 6. Intent 생성
            intent_type = self._determine_intent_type(user_input, property_changes)
            confidence = self._calculate_confidence(property_changes)
            
            intent = NodeEditIntent(
                intent_type=intent_type,
                target_node_id=request.node_id,
                property_changes=property_changes,
                simple_changes=simple_changes,
                original_text=user_input,
                overall_confidence=confidence,
            )
            
            # 7. STPF 평가
            stpf_score = None
            stpf_grade = None
            kelly_recommendation = None
            
            if request.include_stpf_eval:
                try:
                    stpf_result = self._evaluate_stpf(intent, request.current_properties)
                    stpf_score = stpf_result.score_1000
                    stpf_grade = stpf_result.grade
                    intent.stpf_score = stpf_score
                    
                    # STPF 경고 로깅
                    if stpf_score < STPF_DEATH_VALLEY:
                        logger.warning(f"STPF Death Valley: score={stpf_score}")
                    elif stpf_score < STPF_RED_OCEAN:
                        logger.info(f"STPF Red Ocean: score={stpf_score}")
                    
                    # Kelly 권장 계산
                    kelly_result = kelly_allocator.calculate_allocation(
                        user_balance=1000,
                        base_cost=10,
                        success_probability=max(0.1, min(0.9, stpf_result.p_success)),
                        reward_ratio=2.0,
                    )
                    kelly_recommendation = kelly_result.kelly.recommendation
                    
                except Exception as e:
                    logger.error(f"STPF evaluation failed: {e}")
                    # STPF 실패해도 파싱 결과는 반환
            
            # 8. 메트릭 로깅
            parse_time = (time.time() - start_time) * 1000
            logger.info(
                f"Parse success: type={intent_type.value}, "
                f"changes={len(property_changes)}, "
                f"confidence={confidence:.2f}, "
                f"stpf={stpf_score}, "
                f"time={parse_time:.1f}ms"
            )
            
            # 9. 결과 반환
            return IntentParseResult(
                success=True,
                intent=intent,
                intents=[intent] if is_complex else [],
                stpf_score=stpf_score,
                stpf_grade=stpf_grade,
                kelly_recommendation=kelly_recommendation,
                parse_time_ms=parse_time,
            )
            
        except InputValidationError as e:
            self._error_count += 1
            logger.warning(f"Input validation failed: {e}")
            return IntentParseResult(
                success=False,
                error=str(e),
                parse_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            self._error_count += 1
            logger.error(f"Intent parse error: {e}", exc_info=True)
            return IntentParseResult(
                success=False,
                error=f"파싱 오류: {str(e)[:100]}",
                parse_time_ms=(time.time() - start_time) * 1000,
            )
    
    def _validate_and_sanitize_input(self, user_input: str) -> str:
        """입력 검증 및 정규화"""
        if not user_input:
            raise InputValidationError("입력이 비어있습니다")
        
        # 공백 정규화
        sanitized = " ".join(user_input.split())
        
        # 길이 검증
        if len(sanitized) < MIN_INPUT_LENGTH:
            raise InputValidationError(f"입력이 너무 짧습니다 (최소 {MIN_INPUT_LENGTH}자)")
        
        if len(sanitized) > MAX_INPUT_LENGTH:
            logger.warning(f"Input truncated from {len(sanitized)} to {MAX_INPUT_LENGTH}")
            sanitized = sanitized[:MAX_INPUT_LENGTH]
        
        # 위험한 문자 제거 (SQL injection, XSS 방지)
        sanitized = re.sub(r'[<>\'";]', '', sanitized)
        
        return sanitized
    
    def quick_parse(self, user_input: str) -> Dict[str, Any]:
        """빠른 파싱 (API용)"""
        try:
            sanitized = self._validate_and_sanitize_input(user_input)
            _, simple_changes, _ = self._parse_keywords_with_metrics(sanitized)
            return simple_changes
        except InputValidationError as e:
            logger.warning(f"Quick parse validation failed: {e}")
            return {}
    
    def _parse_keywords_with_metrics(
        self,
        user_input: str,
    ) -> Tuple[List[PropertyChange], Dict[str, Any], int]:
        """키워드 기반 파싱 (메트릭 포함)"""
        property_changes = []
        simple_changes = {}
        keyword_count = 0
        
        input_lower = user_input.lower()
        matched_keywords = set()  # 중복 방지
        
        for mapping in self.mappings:
            for keyword in mapping.keywords:
                if keyword in input_lower and keyword not in matched_keywords:
                    matched_keywords.add(keyword)
                    keyword_count += 1
                    
                    for prop_name, prop_value in mapping.property_changes.items():
                        # 중복 속성 처리 (나중 값이 우선)
                        property_changes.append(PropertyChange(
                            property_name=prop_name,
                            category=mapping.category,
                            new_value=prop_value,
                            confidence=mapping.confidence,
                            reason=f"키워드 '{keyword}' 감지",
                        ))
                        simple_changes[prop_name] = prop_value
                    
                    break  # 같은 매핑에서 여러 키워드 감지 방지
        
        logger.debug(f"Keyword matches: {keyword_count}, properties: {len(simple_changes)}")
        return property_changes, simple_changes, keyword_count
    
    def _detect_complex_intent(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """복잡한 의도 감지 (ToT 트리거)"""
        for pattern in self.complex_patterns:
            if re.search(pattern.pattern, user_input):
                return True, pattern.description
        return False, None
    
    def _determine_intent_type(
        self,
        user_input: str,
        property_changes: List[PropertyChange],
    ) -> IntentType:
        """의도 유형 결정"""
        input_lower = user_input.lower()
        
        # 우선순위 순서
        if "삭제" in input_lower or "제거" in input_lower or "지워" in input_lower:
            return IntentType.DELETE
        elif "연결" in input_lower or "이어" in input_lower or "붙여" in input_lower:
            return IntentType.CONNECT
        elif "새로" in input_lower or "추가" in input_lower or "만들" in input_lower or "생성" in input_lower:
            return IntentType.CREATE
        elif "미리보기" in input_lower or "프리뷰" in input_lower or "확인" in input_lower:
            return IntentType.PREVIEW
        elif "취소" in input_lower or "되돌" in input_lower or "원래대로" in input_lower:
            return IntentType.UNDO
        elif len(property_changes) > 3:
            return IntentType.BATCH_EDIT
        else:
            return IntentType.MODIFY
    
    def _calculate_confidence(self, property_changes: List[PropertyChange]) -> float:
        """전체 신뢰도 계산"""
        if not property_changes:
            return MIN_CONFIDENCE_THRESHOLD
        
        confidences = [pc.confidence for pc in property_changes]
        avg_confidence = sum(confidences) / len(confidences)
        
        # 여러 매핑이 일치하면 신뢰도 상승
        if len(property_changes) >= 3:
            avg_confidence = min(1.0, avg_confidence * 1.1)
        
        return max(MIN_CONFIDENCE_THRESHOLD, avg_confidence)
    
    def _evaluate_stpf(
        self,
        intent: NodeEditIntent,
        current_properties: Optional[Dict[str, Any]] = None,
    ):
        """STPF 평가"""
        num_changes = len(intent.property_changes) + len(intent.simple_changes)
        
        # 의도 유형별 리스크 조정
        risk_modifier = 0
        if intent.intent_type == IntentType.DELETE:
            risk_modifier = 3
        elif intent.intent_type == IntentType.BATCH_EDIT:
            risk_modifier = 2
        elif intent.intent_type == IntentType.CREATE:
            risk_modifier = 1
        
        inputs = STPFInputs(
            # Gates
            Trust=8.0,
            Legality=10.0,
            Hygiene=8.0,
            
            # Numerator
            E=min(10.0, 7.0 + intent.overall_confidence),
            K=7.0,
            Nv=5.0,
            Cn=8.0,
            Prf=5.0,
            
            # Denominator
            Cost=min(10.0, 3.0 + num_changes * 0.5),
            Risk=min(10.0, 3.0 + risk_modifier),
            Threat=2.0,
            Pressure=3.0,
            Lag=2.0,
            Uncertainty=4.0,
            
            # Multipliers
            Network=5.0,
            Scarcity=5.0,
            Leverage=6.0,
            
            # Context
            Expectation=6.0,
            Reality=7.0,
        )
        
        return stpf_engine.compute(inputs)
    
    def get_available_mappings(self) -> List[Dict[str, Any]]:
        """사용 가능한 매핑 목록"""
        return [
            {
                "keywords": m.keywords,
                "changes": m.property_changes,
                "category": m.category.value,
            }
            for m in self.mappings
        ]
    
    def add_mapping(self, mapping: IntentMapping) -> None:
        """커스텀 매핑 추가"""
        self.mappings.append(mapping)
        logger.info(f"Mapping added: {mapping.keywords[0]} -> {mapping.property_changes}")
    
    def get_stats(self) -> Dict[str, Any]:
        """파서 통계"""
        return {
            "total_parses": self._parse_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._parse_count),
            "mapping_count": len(self.mappings),
            "complex_patterns": len(self.complex_patterns),
        }


# 싱글톤 인스턴스
intent_parser = IntentParser()
