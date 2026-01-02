"""
Intent API Router (Hardened)

자연어 의도 파싱 API.
입력 검증, 에러 핸들링, 상세 로깅.
"""
import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.services.intent_parser import intent_parser, InputValidationError
from app.schemas.intent_schemas import IntentParseRequest, IntentParseResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intent", tags=["Intent Parser"])


# =========================================================================
# Request Models
# =========================================================================

class QuickParseRequest(BaseModel):
    """빠른 파싱 요청"""
    user_input: str = Field(..., min_length=1, max_length=500)
    node_id: Optional[str] = None
    
    @field_validator('user_input')
    @classmethod
    def validate_input(cls, v: str) -> str:
        """입력 정규화"""
        v = v.strip()
        if not v:
            raise ValueError("입력이 비어있습니다")
        return v


class ParseWithContextRequest(BaseModel):
    """컨텍스트 포함 파싱 요청"""
    user_input: str = Field(..., min_length=1, max_length=1000)
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    current_properties: Optional[Dict[str, Any]] = None
    include_stpf: bool = True
    
    @field_validator('user_input')
    @classmethod
    def validate_input(cls, v: str) -> str:
        """입력 정규화"""
        v = v.strip()
        if not v:
            raise ValueError("입력이 비어있습니다")
        return v


class BatchParseRequest(BaseModel):
    """배치 파싱 요청"""
    inputs: List[str] = Field(..., min_length=1, max_length=20)
    include_stpf: bool = False


# =========================================================================
# Response Models
# =========================================================================

class HealthResponse(BaseModel):
    """상태 응답"""
    status: str
    engine: str
    version: str
    mapping_count: int
    categories: List[str]
    stats: Dict[str, Any]


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/parse", response_model=IntentParseResult)
async def parse_intent(request: ParseWithContextRequest):
    """
    자연어를 노드 편집 의도로 파싱
    
    STPF 평가 및 Kelly 권장 사항 포함
    
    Raises:
        400: 입력 검증 실패
        500: 내부 오류
    """
    start_time = time.time()
    
    try:
        logger.info(f"Intent parse request: {request.user_input[:50]}...")
        
        parse_request = IntentParseRequest(
            user_input=request.user_input,
            node_id=request.node_id,
            node_type=request.node_type,
            current_properties=request.current_properties,
            include_stpf_eval=request.include_stpf,
        )
        
        result = intent_parser.parse(parse_request)
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(
            f"Parse result: success={result.success}, "
            f"stpf_score={result.stpf_score}, "
            f"grade={result.stpf_grade}, "
            f"elapsed={elapsed:.1f}ms"
        )
        
        return result
        
    except InputValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Parse error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파싱 중 오류가 발생했습니다"
        )


@router.post("/quick")
async def quick_parse(request: QuickParseRequest) -> Dict[str, Any]:
    """
    빠른 파싱 (속성 변경만 반환)
    
    STPF 평가 없이 빠르게 변환
    """
    try:
        changes = intent_parser.quick_parse(request.user_input)
        
        return {
            "user_input": request.user_input,
            "changes": changes,
            "change_count": len(changes),
        }
    except Exception as e:
        logger.error(f"Quick parse error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="빠른 파싱 중 오류가 발생했습니다"
        )


@router.post("/batch")
async def batch_parse(request: BatchParseRequest) -> Dict[str, Any]:
    """
    배치 파싱 (다중 입력)
    
    최대 20개 입력까지 지원
    """
    results = []
    success_count = 0
    
    for user_input in request.inputs:
        try:
            parse_result = intent_parser.parse(IntentParseRequest(
                user_input=user_input,
                include_stpf_eval=request.include_stpf,
            ))
            
            results.append({
                "input": user_input,
                "success": parse_result.success,
                "changes": parse_result.intent.to_simple_dict() if parse_result.intent else {},
                "stpf_score": parse_result.stpf_score,
            })
            
            if parse_result.success:
                success_count += 1
                
        except Exception as e:
            results.append({
                "input": user_input,
                "success": False,
                "error": str(e),
            })
    
    return {
        "results": results,
        "total": len(results),
        "success_count": success_count,
        "success_rate": success_count / len(results) if results else 0,
    }


@router.get("/mappings")
async def list_mappings() -> Dict[str, Any]:
    """사용 가능한 의도 매핑 목록"""
    mappings = intent_parser.get_available_mappings()
    
    # 카테고리별 그룹화
    by_category: Dict[str, List] = {}
    for m in mappings:
        cat = m["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append({
            "keywords": m["keywords"],
            "changes": m["changes"],
        })
    
    return {
        "total": len(mappings),
        "by_category": by_category,
    }


@router.post("/test-examples")
async def test_examples() -> Dict[str, Any]:
    """예시 문장 테스트"""
    examples = [
        "이 장면 좀 더 극적으로 해줘",
        "밝게 해줘",
        "카메라 천천히 줌인",
        "색감을 따뜻하게",
        "전체 스토리보드를 더 긴장감 있게 바꿔줘",
    ]
    
    results = []
    for ex in examples:
        parse_result = intent_parser.parse(IntentParseRequest(
            user_input=ex,
            include_stpf_eval=True,
        ))
        
        results.append({
            "input": ex,
            "success": parse_result.success,
            "changes": parse_result.intent.to_simple_dict() if parse_result.intent else {},
            "stpf_score": parse_result.stpf_score,
            "stpf_grade": parse_result.stpf_grade,
        })
    
    return {
        "examples": results,
        "total": len(results),
    }


@router.get("/health", response_model=HealthResponse)
async def health():
    """Intent Parser 상태 및 통계"""
    stats = intent_parser.get_stats()
    
    return HealthResponse(
        status="ok",
        engine="IntentParser",
        version="1.1.0",
        mapping_count=len(intent_parser.mappings),
        categories=list(set(m.category.value for m in intent_parser.mappings)),
        stats=stats,
    )


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """파서 상세 통계"""
    stats = intent_parser.get_stats()
    
    return {
        **stats,
        "mapping_count": len(intent_parser.mappings),
        "complex_patterns": len(intent_parser.complex_patterns),
    }
