"""Vivid App Schema v2 - 범용 앱 설정 스키마.

Hexagonal Architecture + Microkernel Pattern 기반.
DDD Bounded Context 지원.

References:
- MCP Registry Architecture
- 14 Software Architecture Patterns (2025)
- Domain-Driven Design

Usage:
    from config.apps.schema import AppConfig, AppMetadata, Capability
    
    config = AppConfig.from_yaml("config/apps/content/auteurs/bong.yaml")
    if config.has_capability("rag"):
        rag_config = config.get_capability_config("rag")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class AppType(str, Enum):
    """앱 타입 (Bounded Context)."""
    AUTEUR = "auteur"
    DIMENSION = "dimension"
    ANALYTICS = "analytics"
    UTILITY = "utility"
    INTEGRATION = "integration"


class BoundedContext(str, Enum):
    """DDD Bounded Context."""
    CONTENT = "content"      # 콘텐츠 생성 앱
    ANALYTICS = "analytics"  # 분석 앱
    INTEGRATION = "integrations"  # 외부 통합 앱


class CorpusType(str, Enum):
    """코퍼스 유형 (T-Shape vs V-Shape)."""
    T_SHAPE = "t-shape"  # 넓고 얕음 (일반 지식)
    V_SHAPE = "v-shape"  # 좁고 깊음 (전문 지식)


# =============================================================================
# Capability (Microkernel Plugin)
# =============================================================================

@dataclass
class Capability:
    """플러그인 Capability 정의."""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Capability 설정 조회."""
        return self.config.get(key, default)


@dataclass
class RAGCapabilityConfig:
    """RAG Capability 상세 설정."""
    mode: str = "auteur_only"  # always, auteur_only, disabled
    confidence_threshold: float = 0.5
    use_google_search: bool = False
    cache_ttl: int = 3600
    retrieval_strategy: str = "hybrid"  # hybrid, semantic, keyword
    top_k: int = 10
    rerank: bool = True


@dataclass 
class WebhookCapabilityConfig:
    """Webhook Capability 상세 설정."""
    url: Optional[str] = None
    events: List[str] = field(default_factory=list)
    secret: Optional[str] = None


# =============================================================================
# Pipeline Configuration (RAG-as-a-Service)
# =============================================================================

@dataclass
class IngestionConfig:
    """데이터 수집 파이프라인 설정."""
    source: str  # 소스 경로 (gcs://, s3://, file://)
    strategy: str = "semantic"  # semantic, markdown_header, recursive_char
    chunk_size: int = 1024
    chunk_overlap: int = 100
    file_patterns: List[str] = field(default_factory=lambda: ["*.md", "*.txt", "*.pdf"])

@dataclass
class RetrievalConfig:
    """검색 전략 설정."""
    strategy: str = "hybrid"  # hybrid, semantic, keyword
    top_k: int = 10
    score_threshold: float = 0.7
    reranker: Optional[str] = None  # cohere, cross-encoder, vertex
    include_metadata: bool = True

@dataclass
class GenerationConfig:
    """생성 설정."""
    template: str = "default"  # 프롬프트 템플릿 이름 (templates/rag/)
    model: str = "gemini-2.0-flash-exp"  # 기본 모델
    temperature: float = 0.7
    max_tokens: int = 2048
    system_instruction: Optional[str] = None

@dataclass
class PipelineConfig:
    """선언형 RAG 파이프라인 (Level 4)."""
    ingestion: Optional[IngestionConfig] = None
    retrieval: Optional[RetrievalConfig] = None
    generation: Optional[GenerationConfig] = None


# =============================================================================
# Extensions (Hexagonal Adapters - Domain-specific)
# =============================================================================

@dataclass
class CorpusSource:
    """코퍼스 소스 정의."""
    type: str  # source_pack, notebooklm, vertex_ai, gcs
    path: Optional[str] = None
    corpus_name: Optional[str] = None
    notebook_id: Optional[str] = None
    gcs_bucket: Optional[str] = None
    chunking_strategy: str = "semantic"
    chunking_overlap: int = 50


@dataclass
class AuteurExtension:
    """Auteur 도메인 확장 (콘텐츠 앱 전용)."""
    corpus_type: CorpusType = CorpusType.V_SHAPE
    sources: List[CorpusSource] = field(default_factory=list)
    style_hints: Dict[str, Any] = field(default_factory=dict)
    themes: List[str] = field(default_factory=list)


@dataclass
class DimensionExtension:
    """Dimension 도메인 확장 (차원 앱 전용).
    
    10개의 dimension 앱에서 사용:
    - 1D, 2D, 3D, 4D (생성 파이프라인)
    - AD (Aesthetic Director)
    - VEO, QC, STORY, SOUND, AI
    """
    corpus: str = ""  # 거장에 따라 동적 결정
    tool_type: str = "generation"  # generation, analysis, evaluation
    supports_streaming: bool = True
    input_dimensions: List[str] = field(default_factory=list)  # 의존하는 차원
    output_dimensions: List[str] = field(default_factory=list)  # 생성하는 차원


@dataclass
class AnalyticsExtension:
    """Analytics 도메인 확장."""
    metrics: List[str] = field(default_factory=list)
    dashboards: List[str] = field(default_factory=list)
    retention_days: int = 90


@dataclass
class IntegrationExtension:
    """Integration 도메인 확장 (외부 서비스 연동).
    
    사용 예: Slack, Zapier, Webhook 등
    """
    provider: str = ""  # slack, zapier, notion, etc.
    auth_type: str = "api_key"  # oauth2, api_key, bearer
    webhook_url: Optional[str] = None
    rate_limit_per_minute: int = 100
    events: List[str] = field(default_factory=list)  # 구독할 이벤트


@dataclass
class UtilityExtension:
    """Utility 도메인 확장 (범용 유틸리티 앱).
    
    사용 예: 마케팅 어드바이저, 리포트 생성기 등
    """
    service_type: str = "advisor"  # advisor, processor, generator
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    requires_auth: bool = False


@dataclass
class Extensions:
    """도메인별 확장 컨테이너.
    
    각 앱 타입에 맞는 확장을 선택적으로 사용:
    - auteur: Auteur 앱용 (거장 DNA)
    - dimension: Dimension 앱용 (1D-4D, AD, VEO 등)
    - analytics: Analytics 앱용 (대시보드, 메트릭)
    - integration: Integration 앱용 (외부 서비스)
    - utility: Utility 앱용 (범용 유틸리티)
    """
    auteur: Optional[AuteurExtension] = None
    dimension: Optional[DimensionExtension] = None
    analytics: Optional[AnalyticsExtension] = None
    integration: Optional[IntegrationExtension] = None
    utility: Optional[UtilityExtension] = None



# =============================================================================
# Metadata
# =============================================================================

@dataclass
class Display:
    """표시 정보."""
    name_ko: str = ""
    name_en: str = ""
    icon: str = "📦"
    description: str = ""


@dataclass
class AppMetadata:
    """앱 메타데이터."""
    name: str
    type: AppType
    version: str = "1.0.0"
    bounded_context: BoundedContext = BoundedContext.CONTENT
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = AppType(self.type)
        if isinstance(self.bounded_context, str):
            self.bounded_context = BoundedContext(self.bounded_context)


@dataclass
class Keywords:
    """키워드 패턴 (Registry 조회용)."""
    patterns: List[str] = field(default_factory=list)


# =============================================================================
# Main AppConfig
# =============================================================================

@dataclass
class AppConfig:
    """범용 앱 설정 (Microkernel Core)."""
    
    schema_version: str = "vivid-app/v2"
    metadata: AppMetadata = None
    display: Display = field(default_factory=Display)
    capabilities: List[Capability] = field(default_factory=list)
    extensions: Extensions = field(default_factory=Extensions)
    extensions: Extensions = field(default_factory=Extensions)
    pipeline: Optional[PipelineConfig] = None
    keywords: Keywords = field(default_factory=Keywords)
    
    # 내부 상태
    _source_path: Optional[Path] = field(default=None, repr=False)
    
    def has_capability(self, name: str) -> bool:
        """Capability 활성화 여부 확인."""
        for cap in self.capabilities:
            if cap.name == name and cap.enabled:
                return True
        return False
    
    def get_capability(self, name: str) -> Optional[Capability]:
        """Capability 조회."""
        for cap in self.capabilities:
            if cap.name == name:
                return cap
        return None
    
    def get_capability_config(self, name: str) -> Dict[str, Any]:
        """Capability 설정 조회."""
        cap = self.get_capability(name)
        return cap.config if cap else {}
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "AppConfig":
        """YAML 파일에서 AppConfig 로드."""
        path = Path(path)
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        config = cls._from_dict(data)
        config._source_path = path
        return config
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """딕셔너리에서 AppConfig 생성."""
        # Metadata
        meta_data = data.get("metadata", {})
        metadata = AppMetadata(
            name=meta_data.get("name", "unknown"),
            type=meta_data.get("type", "auteur"),
            version=meta_data.get("version", "1.0.0"),
            bounded_context=meta_data.get("bounded_context", "content"),
        )
        
        # Display
        disp_data = data.get("display", {})
        display = Display(
            name_ko=disp_data.get("name_ko", ""),
            name_en=disp_data.get("name_en", ""),
            icon=disp_data.get("icon", "📦"),
            description=disp_data.get("description", ""),
        )
        
        # Capabilities
        capabilities = []
        for cap_data in data.get("capabilities", []):
            capabilities.append(Capability(
                name=cap_data.get("name", ""),
                enabled=cap_data.get("enabled", True),
                config=cap_data.get("config", {}),
            ))
        
        # Extensions
        ext_data = data.get("extensions", {})
        extensions = Extensions()
        
        if "auteur" in ext_data:
            auteur_data = ext_data["auteur"]
            sources = []
            for src in auteur_data.get("sources", []):
                sources.append(CorpusSource(
                    type=src.get("type", "source_pack"),
                    path=src.get("path"),
                    corpus_name=src.get("corpus_name"),
                    notebook_id=src.get("notebook_id"),
                    gcs_bucket=src.get("gcs_bucket"),
                ))
            
            extensions.auteur = AuteurExtension(
                corpus_type=CorpusType(auteur_data.get("corpus_type", "v-shape")),
                sources=sources,
                style_hints=auteur_data.get("style_hints", {}),
                themes=auteur_data.get("themes", []),
            )
        
        # Dimension extension
        if "dimension" in ext_data:
            dim_data = ext_data["dimension"]
            extensions.dimension = DimensionExtension(
                corpus=dim_data.get("corpus", ""),
                tool_type=dim_data.get("tool_type", "generation"),
                supports_streaming=dim_data.get("supports_streaming", True),
                input_dimensions=dim_data.get("input_dimensions", []),
                output_dimensions=dim_data.get("output_dimensions", []),
            )
        
        # Analytics extension
        if "analytics" in ext_data:
            ana_data = ext_data["analytics"]
            extensions.analytics = AnalyticsExtension(
                metrics=ana_data.get("metrics", []),
                dashboards=ana_data.get("dashboards", []),
                retention_days=ana_data.get("retention_days", 90),
            )
        
        # Integration extension
        if "integration" in ext_data:
            int_data = ext_data["integration"]
            extensions.integration = IntegrationExtension(
                provider=int_data.get("provider", ""),
                auth_type=int_data.get("auth_type", "api_key"),
                webhook_url=int_data.get("webhook_url"),
                rate_limit_per_minute=int_data.get("rate_limit_per_minute", 100),
                events=int_data.get("events", []),
            )
        
        # Utility extension
        if "utility" in ext_data:
            util_data = ext_data["utility"]
            extensions.utility = UtilityExtension(
                service_type=util_data.get("service_type", "advisor"),
                input_schema=util_data.get("input_schema", {}),
                output_schema=util_data.get("output_schema", {}),
                requires_auth=util_data.get("requires_auth", False),
            )
        
        # Keywords
        kw_data = data.get("keywords", {})
        keywords = Keywords(patterns=kw_data.get("patterns", []))
        
        # Pipeline
        pipeline = None
        if "pipeline" in data:
            pipe_data = data["pipeline"]
            
            # Ingestion
            ingestion = None
            if "ingestion" in pipe_data:
                ing_data = pipe_data["ingestion"]
                ingestion = IngestionConfig(
                    source=ing_data.get("source", ""),
                    strategy=ing_data.get("strategy", "semantic"),
                    chunk_size=ing_data.get("chunk_size", 1024),
                    chunk_overlap=ing_data.get("chunk_overlap", 100),
                    file_patterns=ing_data.get("file_patterns", ["*.md", "*.txt", "*.pdf"]),
                )
                
            # Retrieval
            retrieval = None
            if "retrieval" in pipe_data:
                ret_data = pipe_data["retrieval"]
                retrieval = RetrievalConfig(
                    strategy=ret_data.get("strategy", "hybrid"),
                    top_k=ret_data.get("top_k", 10),
                    score_threshold=ret_data.get("score_threshold", 0.7),
                    reranker=ret_data.get("reranker"),
                    include_metadata=ret_data.get("include_metadata", True),
                )
                
            # Generation
            generation = None
            if "generation" in pipe_data:
                gen_data = pipe_data["generation"]
                generation = GenerationConfig(
                    template=gen_data.get("template", "default"),
                    model=gen_data.get("model", "gemini-2.0-flash-exp"),
                    temperature=gen_data.get("temperature", 0.7),
                    max_tokens=gen_data.get("max_tokens", 2048),
                    system_instruction=gen_data.get("system_instruction"),
                )
            
            pipeline = PipelineConfig(
                ingestion=ingestion,
                retrieval=retrieval,
                generation=generation,
            )
        
        return cls(
            schema_version=data.get("$schema", "vivid-app/v2"),
            metadata=metadata,
            display=display,
            capabilities=capabilities,
            extensions=extensions,
            pipeline=pipeline,
            keywords=keywords,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        result = {
            "$schema": self.schema_version,
            "metadata": {
                "name": self.metadata.name,
                "type": self.metadata.type.value,
                "version": self.metadata.version,
                "bounded_context": self.metadata.bounded_context.value,
            },
            "display": {
                "name_ko": self.display.name_ko,
                "name_en": self.display.name_en,
                "icon": self.display.icon,
            },
            "capabilities": [
                {"name": c.name, "enabled": c.enabled, "config": c.config}
                for c in self.capabilities
            ],
            "keywords": {"patterns": self.keywords.patterns},
        }
        
        if self.pipeline:
            pipe_dict = {}
            if self.pipeline.ingestion:
                pipe_dict["ingestion"] = {
                    "source": self.pipeline.ingestion.source,
                    "strategy": self.pipeline.ingestion.strategy,
                    "chunk_size": self.pipeline.ingestion.chunk_size,
                    "chunk_overlap": self.pipeline.ingestion.chunk_overlap,
                    "file_patterns": self.pipeline.ingestion.file_patterns,
                }
            if self.pipeline.retrieval:
                pipe_dict["retrieval"] = {
                    "strategy": self.pipeline.retrieval.strategy,
                    "top_k": self.pipeline.retrieval.top_k,
                    "score_threshold": self.pipeline.retrieval.score_threshold,
                    "reranker": self.pipeline.retrieval.reranker,
                    "include_metadata": self.pipeline.retrieval.include_metadata,
                }
            if self.pipeline.generation:
                pipe_dict["generation"] = {
                    "template": self.pipeline.generation.template,
                    "model": self.pipeline.generation.model,
                    "temperature": self.pipeline.generation.temperature,
                    "max_tokens": self.pipeline.generation.max_tokens,
                    "system_instruction": self.pipeline.generation.system_instruction,
                }
            result["pipeline"] = pipe_dict
        
        if self.extensions.auteur:
            result["extensions"] = {
                "auteur": {
                    "corpus_type": self.extensions.auteur.corpus_type.value,
                    "sources": [
                        {"type": s.type, "path": s.path}
                        for s in self.extensions.auteur.sources
                    ],
                    "style_hints": self.extensions.auteur.style_hints,
                    "themes": self.extensions.auteur.themes,
                }
            }
        
        return result


# =============================================================================
# Validation
# =============================================================================

def validate_config(config: AppConfig) -> List[str]:
    """AppConfig 유효성 검증."""
    errors = []
    
    if not config.metadata:
        errors.append("metadata is required")
    elif not config.metadata.name:
        errors.append("metadata.name is required")
    
    if config.metadata and config.metadata.type == AppType.AUTEUR:
        if not config.extensions.auteur:
            errors.append("extensions.auteur is required for auteur type apps")
    
    return errors


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AppType",
    "BoundedContext", 
    "CorpusType",
    "Capability",
    "RAGCapabilityConfig",
    "AuteurExtension",
    "AnalyticsExtension",
    "AuteurExtension",
    "AnalyticsExtension",
    "Extensions",
    "IngestionConfig",
    "RetrievalConfig",
    "GenerationConfig",
    "PipelineConfig",
    "AppMetadata",
    "Display",
    "Keywords",
    "AppConfig",
    "validate_config",
]
