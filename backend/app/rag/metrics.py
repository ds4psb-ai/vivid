"""
RAG 품질 메트릭 수집 모듈

Prometheus 기반 메트릭 수집:
- rag_query_total: RAG 쿼리 총 수
- rag_query_latency_ms: 쿼리 응답 시간
- rag_results_count: 검색 결과 수
- rag_confidence_score: 신뢰도 점수 분포
- rag_cache_hit: 캐시 히트율
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Prometheus 메트릭 (prometheus-client가 설치된 경우에만 활성화)
_metrics_enabled = False
_rag_query_total = None
_rag_cache_hit = None
_rag_latency = None
_rag_results_count = None
_rag_confidence = None

try:
    from prometheus_client import Counter, Histogram
    
    # Counters
    _rag_query_total = Counter(
        "rag_query_total",
        "Total RAG queries",
        ["dimension", "strategy", "source_type"]
    )
    
    _rag_cache_hit = Counter(
        "rag_cache_hit_total",
        "RAG cache hit count",
        ["dimension"]
    )
    
    # Histograms (optimized buckets for long-tail, 2025 best practice)
    _rag_latency = Histogram(
        "rag_query_latency_ms",
        "RAG query latency in milliseconds",
        ["dimension"],
        buckets=[25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000]
    )
    
    _rag_results_count = Histogram(
        "rag_results_count",
        "Number of RAG results returned",
        ["dimension"],
        buckets=[0, 1, 3, 5, 10, 20]
    )
    
    _rag_confidence = Histogram(
        "rag_confidence_score",
        "RAG confidence score distribution",
        ["dimension"],
        buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0]
    )
    
    # Circuit Breaker 메트릭 (2025 Best Practice)
    _circuit_breaker_state = Counter(
        "rag_circuit_breaker_state_total",
        "Circuit breaker state transitions",
        ["state"]  # open, half_open, closed
    )
    
    _circuit_breaker_failures = Counter(
        "rag_circuit_breaker_failures_total",
        "Circuit breaker failure count",
        ["backend"]  # notebooklm, vertex, mcp
    )
    
    # Semantic Cache 메트릭
    _semantic_cache_operations = Counter(
        "rag_semantic_cache_ops_total",
        "Semantic cache operations",
        ["operation", "result", "dimension"]  # P7: Added dimension for tuning reports
    )
    
    _semantic_cache_latency = Histogram(
        "rag_semantic_cache_latency_ms",
        "Semantic cache operation latency",
        ["operation"],
        buckets=[1, 5, 10, 25, 50, 100, 250]
    )
    
    # === Critical Fix: Error Counter (Codex feedback) ===
    _rag_errors_total = Counter(
        "rag_errors_total",
        "Total RAG errors",
        ["dimension", "error_type", "stage"]  # stage: notebooklm, vertex, cache, etc.
    )
    
    # === Critical Fix: Stage Latency (separate from e2e) ===
    _rag_stage_latency = Histogram(
        "rag_stage_latency_ms",
        "RAG stage-specific latency (not e2e)",
        ["stage", "dimension"],  # stage: auteur_first, dimension_query, parallel_query
        buckets=[25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000]
    )
    
    # === Week 3: Router Decision Telemetry ===
    _rag_router_decisions_total = Counter(
        "rag_router_decisions_total",
        "Router strategy decisions count",
        ["strategy", "dimension"]  # strategy: vector, hybrid, auteur_first
    )
    
    _rag_router_score = Histogram(
        "rag_router_score",
        "Router complexity score distribution",
        ["dimension"],
        buckets=[0, 1, 2, 3, 4]
    )
    
    _metrics_enabled = True
    logger.info("RAG Prometheus metrics initialized")
    
except ImportError:
    logger.warning("prometheus-client not installed, RAG metrics disabled")


def record_rag_query(
    dimension: str,
    strategy: str,
    source_type: str,
    latency_ms: float,
    results_count: int,
    confidence: float,
    cache_hit: bool = False,
    auteur_key: Optional[str] = None,
    grounded: bool = False,
    rrf_enabled: bool = False,
) -> None:
    """RAG 쿼리 메트릭 기록.
    
    Args:
        dimension: 차원 코드 (예: "AD", "1D")
        strategy: 검색 전략 (예: "auteur_first", "rrf_hybrid")
        source_type: 소스 유형 (예: "notebooklm", "vertex", "grounding")
        latency_ms: 쿼리 응답 시간 (밀리초)
        results_count: 검색 결과 수
        confidence: 신뢰도 점수 (0.0 - 1.0)
        cache_hit: 캐시 히트 여부
        auteur_key: 거장 키 (옵션)
        grounded: grounding 사용 여부
        rrf_enabled: RRF 융합 사용 여부
    """
    # Prometheus 메트릭 기록
    if _metrics_enabled:
        _rag_query_total.labels(
            dimension=dimension or "unknown",
            strategy=strategy or "unknown",
            source_type=source_type or "unknown"
        ).inc()
        
        _rag_latency.labels(dimension=dimension or "unknown").observe(latency_ms)
        _rag_results_count.labels(dimension=dimension or "unknown").observe(results_count)
        _rag_confidence.labels(dimension=dimension or "unknown").observe(confidence)
        
        if cache_hit:
            _rag_cache_hit.labels(dimension=dimension or "unknown").inc()
    
    # 구조 로깅 (JSON 분석용)
    logger.info(
        "RAG query completed",
        extra={
            "event_type": "rag_query",
            "dimension": dimension,
            "strategy": strategy,
            "source_type": source_type,
            "latency_ms": round(latency_ms, 2),
            "results_count": results_count,
            "confidence": round(confidence, 3),
            "cache_hit": cache_hit,
            "auteur_key": auteur_key,
            "grounded": grounded,
            "rrf_enabled": rrf_enabled,
        }
    )


def record_rag_cache_hit(dimension: str) -> None:
    """RAG 캐시 히트 기록."""
    if _metrics_enabled:
        _rag_cache_hit.labels(dimension=dimension or "unknown").inc()
    
    logger.debug(f"RAG cache hit for dimension: {dimension}")


def record_rag_error(
    dimension: str,
    error_type: str,
    error_message: str,
    stage: str = "unknown",  # NEW: stage parameter
) -> None:
    """RAG 오류 기록.
    
    Args:
        dimension: 차원 코드
        error_type: 에러 타입 (e.g., TimeoutError)
        error_message: 에러 메시지
        stage: 에러 발생 단계 (notebooklm, vertex, cache, etc.)
    """
    # === Critical Fix: Increment Counter ===
    if _metrics_enabled and '_rag_errors_total' in globals():
        _rag_errors_total.labels(
            dimension=dimension or "unknown",
            error_type=error_type,
            stage=stage,
        ).inc()
    
    logger.warning(
        "RAG query error",
        extra={
            "event_type": "rag_error",
            "dimension": dimension,
            "error_type": error_type,
            "error_message": error_message[:200] if error_message else "",
            "stage": stage,
        }
    )


# 메트릭 조회용 헬퍼 (디버깅/테스트용)
def get_metrics_summary() -> dict:
    """현재 메트릭 상태 요약 반환."""
    return {
        "metrics_enabled": _metrics_enabled,
        "prometheus_available": _rag_query_total is not None,
    }


# =============================================================================
# Circuit Breaker 메트릭 (2025 Best Practice)
# =============================================================================

def record_circuit_state(state: str) -> None:
    """Circuit breaker 상태 변경 기록.
    
    Args:
        state: "open", "half_open", "closed"
    """
    if _metrics_enabled and '_circuit_breaker_state' in globals():
        _circuit_breaker_state.labels(state=state).inc()
    logger.info(f"Circuit breaker state: {state}")


def record_circuit_failure(backend: str) -> None:
    """Circuit breaker 실패 기록.
    
    Args:
        backend: "notebooklm", "vertex", "mcp"
    """
    if _metrics_enabled and '_circuit_breaker_failures' in globals():
        _circuit_breaker_failures.labels(backend=backend).inc()


# =============================================================================
# Semantic Cache 메트릭
# =============================================================================

def record_semantic_cache_op(
    operation: str,
    result: str,
    latency_ms: float = 0.0,
    dimension: str = "unknown",  # P7: Added for per-dimension cache reports
) -> None:
    """Semantic cache 연산 기록.
    
    Args:
        operation: "get" or "set"
        result: "hit", "miss", "exact", "semantic"
        latency_ms: 연산 소요 시간
        dimension: 차원 코드 (예: "1D", "AD")
    """
    if _metrics_enabled:
        if '_semantic_cache_operations' in globals():
            _semantic_cache_operations.labels(
                operation=operation,
                result=result,
                dimension=dimension,  # P7
            ).inc()
        if '_semantic_cache_latency' in globals() and latency_ms > 0:
            _semantic_cache_latency.labels(operation=operation).observe(latency_ms)


# =============================================================================
# Router Decision Log (Week 3 - OpenTelemetry Best Practice)
# =============================================================================

import asyncio
import hashlib
import os
import uuid
from datetime import datetime, timezone


def _handle_task_exception(task: asyncio.Task) -> None:
    """Callback to log exceptions from fire-and-forget tasks."""
    try:
        exc = task.exception()
        if exc:
            logger.warning(f"RouterDecisionLog task failed: {exc}")
    except asyncio.CancelledError:
        pass


async def _save_router_decision_async(
    trace_id: str,
    query_hash: str,
    dimension: Optional[str],
    auteur_key: Optional[str],
    strategy: str,
    router_score: int,
    use_reranker: bool,
    use_grounding: bool,
    cache_hit: Optional[bool],
) -> None:
    """Fire-and-forget DB write for router decisions."""
    try:
        from app.database import get_db_context
        from app.models import RouterDecisionLog
        
        async with get_db_context() as db:
            log = RouterDecisionLog(
                trace_id=trace_id,
                query_hash=query_hash,
                dimension=dimension,
                auteur_key=auteur_key,
                strategy=strategy,
                router_score=router_score,
                use_reranker=use_reranker,
                use_grounding=use_grounding,
                cache_hit=cache_hit,
            )
            db.add(log)
            # commit handled by get_db_context()
    except Exception as e:
        logger.warning(f"RouterDecisionLog DB write failed: {e}")


def _make_query_hash(query: str, auteur_key: Optional[str], dimension: Optional[str]) -> str:
    """Generate query hash for router decision log (no PII)."""
    content = f"{query[:500]}|{auteur_key or ''}|{dimension or ''}"
    return hashlib.sha256(content.encode()).hexdigest()  # Full 64 chars (Phase 2)


def _get_trace_context() -> tuple:
    """Get trace_id and span_id from OpenTelemetry context."""
    try:
        from opentelemetry import trace
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            return format(ctx.trace_id, '032x'), format(ctx.span_id, '016x')
    except ImportError:
        pass
    except Exception:
        pass
    # Fallback: generate UUID-based IDs
    fallback = uuid.uuid4().hex
    return fallback[:32], fallback[:16]


def log_router_decision(
    query: str,
    dimension: Optional[str],
    auteur_key: Optional[str],
    router_score: int,
    strategy: str,
    use_reranker: bool,
    use_grounding: bool,
    cache_hit: Optional[bool] = None,
) -> None:
    """Log router decision with OpenTelemetry correlation.
    
    따르는 원칙:
    - 고카디널리티 금지: query 원문 대신 query_hash 사용
    - trace_id 포함: OTel span context에서 추출
    - 1회 기록: hybrid_query에서 router 결정 직후
    """
    trace_id, span_id = _get_trace_context()
    query_hash = _make_query_hash(query, auteur_key, dimension)
    
    # Prometheus 메트릭
    if _metrics_enabled:
        if '_rag_router_decisions_total' in globals():
            _rag_router_decisions_total.labels(
                strategy=strategy,
                dimension=dimension or "unknown",
            ).inc()
        if '_rag_router_score' in globals():
            _rag_router_score.labels(
                dimension=dimension or "unknown",
            ).observe(router_score)
    
    # Structured log (OpenTelemetry aligned)
    logger.info(
        "Router decision",
        extra={
            "event_type": "rag.router.decision",
            "trace_id": trace_id,
            "span_id": span_id,
            "query_hash": query_hash,
            "dimension": dimension or "unknown",
            "auteur_key": auteur_key,
            "router_score": router_score,
            "strategy": strategy,
            "use_reranker": use_reranker,
            "use_grounding": use_grounding,
            "cache_hit": cache_hit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    
    # Phase 2: DB write (fire-and-forget with exception handling)
    if os.getenv("RAG_ROUTER_LOG_SINK") == "db":
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(_save_router_decision_async(
                trace_id=trace_id,
                query_hash=query_hash,
                dimension=dimension,
                auteur_key=auteur_key,
                strategy=strategy,
                router_score=router_score,
                use_reranker=use_reranker,
                use_grounding=use_grounding,
                cache_hit=cache_hit,
            ))
            task.add_done_callback(_handle_task_exception)
        except RuntimeError:
            # No event loop (sync context) - skip silently
            pass


# =============================================================================
# RAG Operation Tracking Decorator (2025 Best Practice)
# =============================================================================

import time
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")


def track_rag_operation(operation_name: str) -> Callable:
    """RAG 연산 자동 추적 데코레이터.
    
    모든 RAG 함수에 일관된 latency/error 측정을 적용합니다.
    
    Usage:
        @track_rag_operation("notebooklm_query")
        async def _query_auteur_first(...):
            ...
    
    Effects:
        - 성공 시: stage latency 기록 (NOT e2e)
        - 실패 시: record_rag_error 자동 호출 with stage
        - 로그: 연산 완료/실패 기록
    
    NOTE: e2e latency는 hybrid_query에서 record_rag_query로 별도 기록됨
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()
            # Dimension can come from kwargs OR be extracted from result
            dimension = kwargs.get("dimension", "unknown")
            
            try:
                result = await func(*args, **kwargs)
                latency_ms = (time.monotonic() - start) * 1000
                
                # === Critical Fix: Use STAGE latency, NOT e2e ===
                if _metrics_enabled and '_rag_stage_latency' in globals():
                    _rag_stage_latency.labels(
                        stage=operation_name,
                        dimension=dimension,
                    ).observe(latency_ms)
                
                logger.debug(
                    f"[RAG-Track] {operation_name} completed | "
                    f"latency={latency_ms:.1f}ms | dimension={dimension}"
                )
                return result
                
            except Exception as e:
                latency_ms = (time.monotonic() - start) * 1000
                
                # === Critical Fix: Include stage in error ===
                record_rag_error(
                    dimension=dimension,
                    error_type=type(e).__name__,
                    error_message=str(e)[:200],
                    stage=operation_name,  # NEW: stage parameter
                )
                
                logger.warning(
                    f"[RAG-Track] {operation_name} failed | "
                    f"error={type(e).__name__} | latency={latency_ms:.1f}ms"
                )
                raise
                
        return wrapper
    return decorator
