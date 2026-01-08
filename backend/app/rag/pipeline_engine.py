"""Pipeline Engine - 선언형 RAG 파이프라인 실행기.

YAML로 정의된 파이프라인 설정을 읽어 기존 RAG 서비스를 실행합니다.
기존 코드를 수정하지 않고 래핑하여 사용합니다.

Usage:
    from app.rag.pipeline_engine import PipelineEngine
    from app.core.app_registry import AppRegistry
    
    app = AppRegistry.get_by_name("marketing_advisor")
    engine = PipelineEngine(app)
    result = await engine.query("마케팅 전략")
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.app_schema import AppConfig, PipelineConfig
from app.rag.hybrid_rag import get_hybrid_rag_service, HybridRAGResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """파이프라인 실행 결과."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    pipeline_name: str
    strategy_used: str


class PipelineEngine:
    """선언형 RAG 파이프라인 엔진.
    
    YAML 설정을 기반으로 기존 RAG 서비스를 호출합니다.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.app_name = config.metadata.name
        self.pipeline = config.pipeline
        
    async def query(self, query: str, **kwargs) -> PipelineResult:
        """파이프라인 실행.
        
        Args:
            query: 사용자 쿼리
            **kwargs: 추가 옵션
            
        Returns:
            PipelineResult
        """
        logger.info(f"[PipelineEngine] Running pipeline: {self.app_name}")
        
        # 파이프라인 설정에서 전략 결정
        retrieval_strategy = "hybrid"
        if self.pipeline and self.pipeline.retrieval:
            retrieval_strategy = self.pipeline.retrieval.strategy
            
        # 기존 HybridRAGService 사용
        service = get_hybrid_rag_service()
        result: HybridRAGResult = await service.query(
            query=query,
            use_google_search=kwargs.get("use_google_search", True),
        )
        
        # 소스 통합
        sources = []
        for src in result.vertex_sources:
            sources.append({
                "content": src.content,
                "score": src.relevance_score,
                "source": src.document_name,
            })
        for src in result.notebooklm_sources:
            sources.append({
                "content": src.content,
                "score": src.confidence,
                "source": src.source_id,
            })
            
        return PipelineResult(
            answer=result.answer,
            sources=sources,
            confidence=result.confidence,
            pipeline_name=self.app_name,
            strategy_used=retrieval_strategy,
        )


# Registry 기반 파이프라인 조회
_pipeline_cache: Dict[str, PipelineEngine] = {}


def get_pipeline(app_name: str) -> Optional[PipelineEngine]:
    """앱 이름으로 파이프라인 엔진 조회.
    
    Args:
        app_name: 앱 이름
        
    Returns:
        PipelineEngine or None
    """
    if app_name in _pipeline_cache:
        return _pipeline_cache[app_name]
        
    from app.core.app_registry import AppRegistry
    
    config = AppRegistry.get_by_name(app_name)
    if not config:
        logger.warning(f"[PipelineEngine] App not found: {app_name}")
        return None
        
    engine = PipelineEngine(config)
    _pipeline_cache[app_name] = engine
    
    return engine
